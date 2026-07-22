#!/usr/bin/env python3
"""Unit tests for the monthly newsletter assembly.

Dependency-free (stdlib unittest), so CI runs them with no install step. These
exercise the pure logic with fixtures; they never touch git, the network, or the
Loops API.

Run:  python3 tools/test_newsletter_draft.py
"""

import datetime as dt
import unittest

import newsletter_draft as nd

# A stable set of Quentin's own styling notes (shape of ideas.yaml notes.items).
NOTES = [
    {"title": "Dress with intent", "body": "Does this help me become who I am becoming?"},
    {"title": "Release what no longer fits", "body": "Letting go of old clothes is honest."},
    {"title": "Confidence is a skill", "body": "How you walk into a room can be practiced."},
]

# June 2026 is the target month across these tests.
JUNE = "2026-06"


def ledger(incorporated=None, trimmed=None):
    return {
        "profile": "mrqfears",
        "incorporated": incorporated or [],
        "skipped": [],
        "trimmed": trimmed or [],
    }


class NormalMonth(unittest.TestCase):
    """A normal month with new work: a draft is created."""

    def test_creates_draft_with_news_and_tip(self):
        led = ledger(
            incorporated=[
                {"shortcode": "A1", "date": "2026-06-08", "decision": "add",
                 "target": "content/galleries.yaml", "reason": "New editorial shoot with a bold color story"},
                {"shortcode": "A2", "date": "2026-06-20", "decision": "add",
                 "target": "content/ideas.yaml", "reason": "A note on dressing for the room you want"},
            ],
        )
        draft = nd.build_draft(led, commits=[], notes=NOTES, month=JUNE)
        self.assertIsNotNone(draft)
        self.assertEqual(draft.news_count, 2)
        self.assertIn("New editorial shoot", draft.text)
        # Leads with a styling tip drawn from Quentin's own notes.
        self.assertIn(draft.tip_title, [n["title"] for n in NOTES])
        self.assertIn(draft.tip_title, draft.subject)

    def test_body_has_no_em_dash_or_placeholder(self):
        led = ledger(
            incorporated=[
                {"date": "2026-06-08", "decision": "add", "target": "content/work.yaml",
                 "reason": "A new case study on a menswear campaign"},
            ],
        )
        draft = nd.build_draft(led, commits=[], notes=NOTES, month=JUNE)
        self.assertEqual(nd.find_problems(draft), [])


class ZeroChangeMonth(unittest.TestCase):
    """A month with nothing new: NO draft is created."""

    def test_no_draft_when_empty(self):
        draft = nd.build_draft(ledger(), commits=[], notes=NOTES, month=JUNE)
        self.assertIsNone(draft)

    def test_no_draft_when_only_out_of_window(self):
        led = ledger(
            incorporated=[
                {"date": "2026-05-30", "decision": "add", "target": "content/work.yaml",
                 "reason": "Last month's work, not this month's"},
            ],
        )
        draft = nd.build_draft(led, commits=[], notes=NOTES, month=JUNE)
        self.assertIsNone(draft)

    def test_no_draft_when_only_skips(self):
        led = ledger(
            incorporated=[
                {"date": "2026-06-10", "decision": "skip", "target": "post",
                 "reason": "Off brand, personal post"},
            ],
        )
        draft = nd.build_draft(led, commits=[], notes=NOTES, month=JUNE)
        self.assertIsNone(draft)


class TrimsAndReplacementsMonth(unittest.TestCase):
    """A month of only trims and replacements: replacements are news, trims are not."""

    def test_replacements_are_news_trims_are_excluded(self):
        led = ledger(
            incorporated=[
                {"date": "2026-06-12", "decision": "replace", "target": "content/galleries.yaml",
                 "reason": "A sharper studio portrait replaced a weaker frame",
                 "replaced": "old.jpg", "why_out": "softer light"},
            ],
            trimmed=[
                {"date": "2026-06-12", "target": "content/ideas.yaml",
                 "reason": "Removed a redundant note", "decision": "trim"},
            ],
        )
        draft = nd.build_draft(led, commits=[], notes=NOTES, month=JUNE)
        self.assertIsNotNone(draft)
        self.assertEqual(draft.news_count, 1)
        self.assertIn("sharper studio portrait", draft.text)
        # The trim must not appear as announced news.
        self.assertNotIn("Removed a redundant note", draft.text)

    def test_trim_commit_subjects_are_not_news(self):
        led = ledger()
        commits = [
            {"date": "2026-06-15", "subject": "Trim weak gallery image from editorial (#40)"},
            {"date": "2026-06-16", "subject": "Remove stale upcoming-event copy (#41)"},
        ]
        draft = nd.build_draft(led, commits=commits, notes=NOTES, month=JUNE)
        # Only trims/removals this month -> nothing to announce -> no draft.
        self.assertIsNone(draft)


class Assembly(unittest.TestCase):
    """Lower-level behaviours of the assembly helpers."""

    def test_commits_supplement_and_dedupe(self):
        led = ledger(
            incorporated=[
                {"date": "2026-06-08", "decision": "add", "target": "content/work.yaml",
                 "reason": "Added a new campaign case study"},
            ],
        )
        commits = [
            {"date": "2026-06-09", "subject": "Added a new campaign case study (#42)"},  # dupe
            {"date": "2026-06-10", "subject": "Add three new speaking dates (#43)"},     # new
        ]
        news = nd.assemble_news(led, commits, dt.date(2026, 6, 1), dt.date(2026, 6, 30))
        texts = [n.text for n in news]
        self.assertEqual(len(news), 2)
        self.assertTrue(any("campaign case study" in t for t in texts))
        self.assertTrue(any("speaking dates" in t for t in texts))

    def test_news_capped_at_max(self):
        led = ledger(
            incorporated=[
                {"date": f"2026-06-{d:02d}", "decision": "add", "target": "content/work.yaml",
                 "reason": f"News item number {d}"}
                for d in range(1, 9)
            ],
        )
        news = nd.assemble_news(led, [], dt.date(2026, 6, 1), dt.date(2026, 6, 30))
        self.assertEqual(len(news), nd.MAX_NEWS)

    def test_href_points_at_relevant_page(self):
        led = ledger(
            incorporated=[
                {"date": "2026-06-08", "decision": "add", "target": "content/ideas.yaml",
                 "reason": "A new note on style"},
            ],
        )
        news = nd.assemble_news(led, [], dt.date(2026, 6, 1), dt.date(2026, 6, 30))
        self.assertTrue(news[0].href.endswith("/ideas"))

    def test_tip_rotates_by_seed(self):
        seen = {nd.select_tip(NOTES, seed)[0] for seed in range(len(NOTES))}
        self.assertEqual(len(seen), len(NOTES))  # each note used once per cycle


class Window(unittest.TestCase):
    def test_previous_month_default(self):
        start, end, label = nd.month_window(None, today=dt.date(2026, 7, 3))
        self.assertEqual((start, end), (dt.date(2026, 6, 1), dt.date(2026, 6, 30)))
        self.assertEqual(label, "June 2026")

    def test_explicit_month(self):
        start, end, _ = nd.month_window("2026-02", today=dt.date(2026, 7, 3))
        self.assertEqual((start, end), (dt.date(2026, 2, 1), dt.date(2026, 2, 28)))


if __name__ == "__main__":
    unittest.main()
