#!/usr/bin/env python3
"""Assemble the monthly newsletter and create it as a DRAFT in Loops.

The house rule is absolute: this tool never sends anything. It creates a draft
via the Loops Campaign API (POST /v1/campaigns) and stops. A human opens Loops,
reads the draft, and hits send. Silence is not approval.

Shape of the email (kept deliberately short):
  1. A lead: one styling idea, drawn from Quentin's own notes in
     content/ideas.yaml. His words, not invented opinions.
  2. "What's new": two or three items from the month, assembled from
     instagram-ledger.json (what the weekly curation routine decided) and the
     git history of content/*.yaml. A link back to the site.

The window is a calendar month. By default the tool looks at the previous
calendar month relative to today; pass --month YYYY-MM to target another. Using
whole-month windows means each run covers a distinct period, so no state file is
needed and news is never double-reported across months.

If a month has nothing new to report, the tool writes NOTHING. No draft is the
correct outcome (a padded newsletter is worse than no newsletter). That is an
explicit branch: `build_draft` returns None when there is no news, and the CLI
creates no campaign.

Design split so the logic is unit-testable without network, git, or a YAML
dependency: the pure functions (assemble_news, select_tip, render_email,
build_draft, find_problems) take plain Python data. Only the CLI edges read the
real files, shell out to git, and call the Loops API.

Secrets: the Loops API key is read from the LOOPS_API_KEY environment variable
(a GitHub Actions secret). It is never written to a file, a log, or the draft.

Usage:
  python3 tools/newsletter_draft.py --dry-run          # render to a local file, no API
  python3 tools/newsletter_draft.py --month 2026-06    # target a specific month
  python3 tools/newsletter_draft.py                    # create the draft in Loops
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

# ---- Config -----------------------------------------------------------------
SITE_URL = "https://quentinfears.com"
LOOPS_API_BASE = "https://app.loops.so/api/v1"
MAX_NEWS = 3  # keep it short: two or three items

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Markers that must never survive into a finished draft. If any appears, the
# body was assembled from an unfilled template and must not go out.
PLACEHOLDER_MARKERS = (
    "replace_with", "{{", "}}", "todo", "tktk", "tbd",
    "lorem ipsum", "<placeholder", "xxxx", "your name here",
)
EM_DASH = "—"
EM_DASH_ENTITIES = ("&mdash;", "&#8212;", "&#x2014;")

# Words that mark a commit as an editorial removal, not news to announce.
_TRIM_PREFIXES = ("trim", "remove", "delete", "drop", "retire", "prune")


@dataclass
class NewsItem:
    text: str
    href: str


@dataclass
class Draft:
    subject: str
    html: str
    text: str
    tip_title: str
    news_count: int


# ---- Window -----------------------------------------------------------------
def month_window(month: str | None, today: dt.date | None = None) -> tuple[dt.date, dt.date, str]:
    """Return (first_day, last_day, label) for the target month.

    `month` is "YYYY-MM"; when None, the previous calendar month of `today`.
    """
    today = today or dt.date.today()
    if month:
        year, mon = (int(p) for p in month.split("-"))
    else:
        first_this = today.replace(day=1)
        prev_last = first_this - dt.timedelta(days=1)
        year, mon = prev_last.year, prev_last.month
    last = calendar.monthrange(year, mon)[1]
    start = dt.date(year, mon, 1)
    end = dt.date(year, mon, last)
    label = start.strftime("%B %Y")
    return start, end, label


def _parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()[:10]
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# ---- News assembly ----------------------------------------------------------
_PAGE_KEYWORDS = (
    ("ideas", "ideas"),
    ("galler", "work"),
    ("work", "work"),
    ("speak", "speak"),
    ("host", "speak"),
    ("about", "about"),
)


def _href_for(target: str, site_url: str) -> str:
    """Best-guess a link back to the page a change landed on."""
    low = (target or "").lower()
    for needle, page in _PAGE_KEYWORDS:
        if needle in low:
            return f"{site_url}/{page}"
    return f"{site_url}/"


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _clean_subject(subject: str) -> str:
    # Drop a trailing PR number like " (#25)".
    return re.sub(r"\s*\(#\d+\)\s*$", "", subject).strip()


def assemble_news(
    ledger: dict,
    commits: list[dict],
    start: dt.date,
    end: dt.date,
    site_url: str = SITE_URL,
    max_news: int = MAX_NEWS,
) -> list[NewsItem]:
    """Build the "what's new" list from the ledger and content commits.

    Only additions and replacements count as news: an `add` or `replace` in the
    ledger put new work on the site. Trims (pure removals) are editorial and are
    never announced, so a month of only trims yields no news.
    """
    news: list[NewsItem] = []
    seen: list[str] = []

    def add(text: str, href: str) -> None:
        text = text.strip().rstrip(".")
        if not text:
            return
        norm = _normalize(text)
        for prior in seen:
            if norm == prior or norm in prior or prior in norm:
                return
        seen.append(norm)
        news.append(NewsItem(text=text, href=href))

    # 1) Structured decisions from the weekly curation routine.
    incorporated = ledger.get("incorporated") or []
    dated = []
    for entry in incorporated:
        if (entry.get("decision") or "").lower() not in ("add", "replace"):
            continue
        d = _parse_date(entry.get("date", ""))
        if d is None or not (start <= d <= end):
            continue
        dated.append((d, entry))
    for _, entry in sorted(dated, key=lambda t: t[0], reverse=True):
        headline = (entry.get("reason") or entry.get("target") or "").strip()
        add(headline, _href_for(entry.get("target", ""), site_url))

    # 2) Supplement from content/*.yaml commits, newest first, skipping trims.
    dated_commits = []
    for commit in commits:
        d = _parse_date(commit.get("date", ""))
        if d is None or not (start <= d <= end):
            continue
        dated_commits.append((d, commit))
    for _, commit in sorted(dated_commits, key=lambda t: t[0], reverse=True):
        subject = _clean_subject(commit.get("subject", ""))
        if not subject:
            continue
        first = _normalize(subject).split(" ")[:1]
        if first and first[0] in _TRIM_PREFIXES:
            continue
        add(subject, _href_for(subject, site_url))

    return news[:max_news]


# ---- Styling tip ------------------------------------------------------------
def select_tip(notes: list[dict], seed: int) -> tuple[str, str]:
    """Pick one styling note deterministically, rotating by month.

    `notes` is the list of {title, body} from content/ideas.yaml. The rotation
    means a different note leads each month; the words are always Quentin's.
    """
    usable = [n for n in notes if (n.get("title") or "").strip() and (n.get("body") or "").strip()]
    if not usable:
        raise ValueError("no usable styling notes found in ideas.yaml notes.items")
    note = usable[seed % len(usable)]
    return note["title"].strip(), note["body"].strip()


# ---- Render -----------------------------------------------------------------
def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_email(
    tip_title: str,
    tip_body: str,
    news: list[NewsItem],
    site_url: str,
    month_label: str,
) -> Draft:
    """Render the subject + HTML + plain-text bodies. Kept short and on-voice."""
    subject = f"Style notes: {tip_title}"

    lead = "Here is one idea to use this week, and a quick note on what is new."

    # HTML: semantic, inline-friendly, no external assets. Loops wraps this with
    # the sender template and appends the unsubscribe link + address footer.
    html_parts = [
        f'<p style="color:#666">{_esc(lead)}</p>',
        '<p style="text-transform:uppercase;letter-spacing:0.16em;font-size:12px;color:#999">'
        "This month's styling note</p>",
        f"<h2>{_esc(tip_title)}</h2>",
        f"<p>{_esc(tip_body)}</p>",
    ]
    text_parts = [lead, "", "THIS MONTH'S STYLING NOTE", tip_title, tip_body]

    if news:
        html_parts.append(
            '<p style="text-transform:uppercase;letter-spacing:0.16em;font-size:12px;'
            'color:#999">What is new</p>'
        )
        html_parts.append("<ul>")
        text_parts += ["", "WHAT IS NEW"]
        for item in news:
            html_parts.append(
                f'<li><a href="{_esc(item.href)}">{_esc(item.text)}</a></li>'
            )
            text_parts.append(f"- {item.text} ({item.href})")
        html_parts.append("</ul>")

    html_parts.append(
        f'<p><a href="{_esc(site_url)}">See more on the site</a></p>'
    )
    html_parts.append("<p>Quentin</p>")
    text_parts += ["", f"See more on the site: {site_url}", "", "Quentin"]

    return Draft(
        subject=subject,
        html="\n".join(html_parts),
        text="\n".join(text_parts),
        tip_title=tip_title,
        news_count=len(news),
    )


def find_problems(draft: Draft) -> list[str]:
    """Guard the finished draft: no em dash, no unfilled placeholder."""
    problems: list[str] = []
    blob = "\n".join([draft.subject, draft.html, draft.text])
    low = blob.lower()
    if EM_DASH in blob or any(e in low for e in EM_DASH_ENTITIES):
        problems.append("em dash in the email body (restructure the sentence instead)")
    for marker in PLACEHOLDER_MARKERS:
        if marker in low:
            problems.append(f"unfilled placeholder in the email body: {marker!r}")
    return problems


# ---- Orchestration ----------------------------------------------------------
def build_draft(
    ledger: dict,
    commits: list[dict],
    notes: list[dict],
    month: str | None = None,
    today: dt.date | None = None,
    site_url: str = SITE_URL,
) -> Draft | None:
    """Assemble the draft, or return None when the month has no news.

    None is the "nothing worth saying, write nothing" branch: no news means no
    draft, full stop. The styling tip is the lead when we do send, but it never
    justifies sending on its own.
    """
    start, end, label = month_window(month, today)
    news = assemble_news(ledger, commits, start, end, site_url=site_url)
    if not news:
        return None
    seed = start.year * 12 + (start.month - 1)
    tip_title, tip_body = select_tip(notes, seed)
    draft = render_email(tip_title, tip_body, news, site_url, label)
    problems = find_problems(draft)
    if problems:
        raise ValueError("draft failed content checks: " + "; ".join(problems))
    return draft


# ---- Edges: files, git, API -------------------------------------------------
def load_ledger(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_notes(ideas_yaml_path: str) -> list[dict]:
    """Read notes.items (title/body) from content/ideas.yaml.

    Uses PyYAML when available; otherwise a minimal fallback that reads just the
    notes.items list, so the tool has no hard third-party dependency.
    """
    with open(ideas_yaml_path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return (data.get("notes") or {}).get("items") or []
    except ImportError:
        return _fallback_parse_notes(text)


def _fallback_parse_notes(text: str) -> list[dict]:
    """Tiny parser for the notes.items block only (title/body, single-line)."""
    lines = text.splitlines()
    items: list[dict] = []
    in_notes = in_items = False
    cur: dict | None = None

    def unquote(v: str) -> str:
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        return v

    for line in lines:
        if re.match(r"^notes:\s*$", line):
            in_notes, in_items = True, False
            continue
        if in_notes and re.match(r"^\S", line) and not line.startswith("notes:"):
            break  # left the notes block
        if in_notes and re.match(r"^\s+items:\s*$", line):
            in_items = True
            continue
        if in_items:
            m = re.match(r"^\s*-\s*title:\s*(.+)$", line)
            if m:
                if cur:
                    items.append(cur)
                cur = {"title": unquote(m.group(1))}
                continue
            m = re.match(r"^\s*body:\s*(.+)$", line)
            if m and cur is not None:
                cur["body"] = unquote(m.group(1))
    if cur:
        items.append(cur)
    return items


def git_content_commits(start: dt.date, end: dt.date, repo_root: str = _REPO_ROOT) -> list[dict]:
    """Commits touching content/*.yaml in [start, end], as {date, subject}."""
    until = end + dt.timedelta(days=1)  # git --until is exclusive of the day boundary
    try:
        out = subprocess.check_output(
            [
                "git", "log",
                f"--since={start.isoformat()}",
                f"--until={until.isoformat()}",
                "--date=short",
                "--pretty=%ad%x09%s",
                "--", "content/",
            ],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    commits = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        date, subject = line.split("\t", 1)
        commits.append({"date": date.strip(), "subject": subject.strip()})
    return commits


def create_loops_draft(api_key: str, draft: Draft, base: str = LOOPS_API_BASE) -> dict:
    """Create a DRAFT campaign in Loops. Never sends.

    POST /v1/campaigns. The exact request body is confirmed against
    loops.so/docs/api-reference/create-campaign; because no Loops page states the
    Campaign API is on by default for a brand-new free team, the first real call
    is the test of that. This keeps the request in one place so it is easy to
    adjust after that first call. The API key is only ever sent in the auth
    header, never logged.
    """
    payload = {
        "name": draft.subject,
        "subject": draft.subject,
        "body": draft.html,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/campaigns",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(
            f"Loops API returned HTTP {exc.code}. If this is 401/403, the "
            f"Campaign API may not be enabled for this free team. Response: {detail}"
        ) from None


def _emit_output(drafted: bool, subject: str = "", preview_path: str = "") -> None:
    """Expose the result to a GitHub Actions step, if running in one."""
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(f"drafted={'true' if drafted else 'false'}\n")
        fh.write(f"subject={subject}\n")
        fh.write(f"preview={preview_path}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Assemble the monthly newsletter draft.")
    ap.add_argument("--month", help="Target month YYYY-MM (default: previous calendar month).")
    ap.add_argument("--dry-run", action="store_true", help="Render to a file; do not call Loops.")
    ap.add_argument("--out", default=os.path.join(_REPO_ROOT, "newsletter-preview.txt"),
                    help="Where to write the preview (dry-run and after a real draft).")
    args = ap.parse_args(argv)

    ledger = load_ledger(os.path.join(_REPO_ROOT, "instagram-ledger.json"))
    notes = load_notes(os.path.join(_REPO_ROOT, "content", "ideas.yaml"))
    start, end, label = month_window(args.month)
    commits = git_content_commits(start, end)

    draft = build_draft(ledger, commits, notes, month=args.month)

    if draft is None:
        print(f"No news for {label}. Writing nothing (this is the correct outcome).")
        _emit_output(drafted=False)
        return 0

    preview = (
        f"SUBJECT: {draft.subject}\n"
        f"MONTH:   {label}\n"
        f"NEWS:    {draft.news_count} item(s)\n"
        f"{'-' * 60}\n{draft.text}\n{'-' * 60}\n\nHTML:\n{draft.html}\n"
    )
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(preview)
    print(f"Draft for {label} rendered to {args.out}")
    print(f"Subject: {draft.subject}")

    if args.dry_run:
        print("Dry run: no Loops campaign created.")
        _emit_output(drafted=False, subject=draft.subject, preview_path=args.out)
        return 0

    api_key = os.environ.get("LOOPS_API_KEY")
    if not api_key:
        print("LOOPS_API_KEY is not set; cannot create the draft.", file=sys.stderr)
        return 1
    result = create_loops_draft(api_key, draft)
    print(f"Created Loops draft campaign (id: {result.get('id', 'unknown')}). Nothing was sent.")
    _emit_output(drafted=True, subject=draft.subject, preview_path=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
