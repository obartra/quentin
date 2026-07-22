# CLAUDE.md

Working notes for this repo. Human-facing overview is in [README.md](README.md); the
repositioning rationale is in [PROPOSAL.md](PROPOSAL.md); the image/media manifest is
in [ASSETS.md](ASSETS.md); the build architecture is in
[docs/astro-keystatic-migration.md](docs/astro-keystatic-migration.md).

## What this is

A marketing site for Quentin Fears that keeps a dark, editorial visual style while
repositioning him from "celebrity & personal stylist" to fashion creative leader,
visual strategist, speaker, and host. Six pages (`index`, `work`, `ideas`, `speak`,
`about`, `contact`).

It is built with **Astro**, and all copy lives in editable content files managed by a
**Keystatic** admin, so the site is maintainable with no code. Astro renders the
content into the same markup the site shipped by hand and reuses the same
self-contained CSS/JS, so the output, the SEO layer, and the galleries are
unchanged. The build is a static export deployed to GitHub Pages.

## How you work: owner-driven and autonomous

The site owner is non-technical and runs everything by plain-language request. They
should never have to know or say the words "branch", "commit", "PR", or "merge", and
should never have to open a terminal or know one exists — that plumbing is your job.
Their part is to say what they want and to approve the result; your part is everything
else, end to end, including getting it live.

Follow this loop for every change, without being asked for each step:

1. **Work on a branch, always cut from the latest `main`.** Never push to `main`
   directly: it is protected and rejects direct pushes. Changes reach it only through a
   pull request. Keeping current with `main` is your job, never the owner's to ask
   about: `git fetch origin main` before you start, and before you merge, rebase your
   branch onto the latest `main` (`git rebase origin/main`) and resolve any conflicts
   yourself so the PR always merges cleanly. If `main` moves while a PR is open, rebase
   again rather than letting it go stale.
2. **Validate thoroughly before showing it.** `npm run build`, then
   `python3 tools/validate_site.py dist` and `python3 tools/seo_check.py dist`; both
   must pass clean. Re-run until green. For anything visible, look at the built page,
   not just the YAML.
3. **Show the owner and get approval, without ever sending them to a terminal.** They
   should not have to run anything or know the command line exists. Preview the change
   *for* them: build and open the site in the pre-installed browser (Chromium via
   Playwright), capture screenshots of the affected pages, and send those; or point
   them at the PR's live Netlify deploy-preview link, which they can just click.
   Describe in plain terms what changed. They approve *what* changed, not the
   mechanics. Skip this only when they already approved the change in the same request.
4. **Open a pull request** and let CI run both validators on it.
5. **Merge it yourself once CI is green and the owner has approved.** Merging into
   `main` is what deploys the site to GitHub Pages, so a change is not done until it
   is merged and the deploy succeeds. Never leave an approved, green PR sitting
   unmerged waiting for the owner to click a button: they may not know to. Then
   report back with the live result.

If anything blocks the loop (missing access, a check you cannot fix, a genuinely
ambiguous request), stop and say so in one plain sentence with one direct question.
Do not narrate the plumbing; report outcomes.

**Maintain this file as you go.** When the owner gives feedback about how you should
work, fold it into CLAUDE.md immediately, in the section it belongs to. Keep the file
lean: group related guidance, trim redundancy, and delete anything no longer true.
Treat length as a cost, and prefer editing an existing line over adding a new one; a
short, current file beats a growing one.

This depends on two things staying set up (see [docs/hosted-admin.md](docs/hosted-admin.md)):

- The **Claude GitHub App** installed on `qafears/website` with **Contents: Read &
  write**. Without it, every push and merge fails with a 403.
- `main` protected so changes must go through a PR. That is deliberate; keep it. It is
  also why the flow above is always PR-then-merge, never a direct push.

## Stack & conventions

- **Astro** (static output, `build.format: 'file'` → flat `about.html`, `work.html`,
  …). `npm run build` emits `dist/`; that is what deploys and what the validators
  check. URLs are extensionless: links, canonicals, and the sitemap say `work`, and
  the static host (GitHub Pages, Netlify, and Astro's dev/preview servers) serves
  `work.html` for it. The old `.html` URLs still resolve since the files exist.
- **Content is data.** Editable text and image paths live in `content/*.yaml`, one
  singleton per page plus a `galleries` singleton. The schema and the `/keystatic`
  admin are defined in [keystatic.config.ts](keystatic.config.ts). Pages read it at
  build time via `@keystatic/core/reader` (see [src/lib/content.ts](src/lib/content.ts));
  no server or database.
- **The design system and behavior are unchanged and self-contained.** CSS in
  `public/assets/css/style.css`; behavior in `public/assets/js/main.js` (mobile nav,
  scroll-reveal, gallery lightbox, contact-form FormSubmit AJAX handler, footer
  year). No external fonts, scripts, or CDNs, with **one sanctioned exception:
  Google Analytics** (see "Analytics" below). Everything else must keep working
  offline and CSP-safe. Pages stay legible with JavaScript disabled, and they
  render fine even when the GA request is blocked. Everything in `public/` ships
  verbatim into `dist/`.
- **Keep links relative.** Every internal link and asset reference is relative
  (`work`, `assets/css/style.css`, `favicon.svg`) so the site works under both
  the GitHub Pages subpath and the apex domain. `base` stays `/`; do not switch to
  root-absolute asset paths. Page links are extensionless (`work`, not `work.html`);
  the home link is `./`.
- **Never use em dashes in copy** — not in page content, titles, metadata, alt text,
  UI strings, or anything else that ships. Restructure the sentence instead: a comma,
  colon, or period in prose, a pipe in titles. `tools/validate_site.py` fails CI on
  any em dash (or `&mdash;` entity) in the built output. The house voice keeps the
  all-caps letter-spaced labels and the editorial tone; it just makes its cuts with
  other punctuation.
- Keep metadata honest and present-day. No Wix boilerplate ("Mysite", "Cordan", lorem
  ipsum) — CI fails on it.

## The Keystatic admin

Three build shapes from one project (see the header comment in
[astro.config.mjs](astro.config.mjs)):

- **Local editing:** `npm run dev` → `/keystatic`. Local file storage; editing writes
  the `content/*.yaml` files; commit + push to publish. Free, no server.
- **Public site:** `npm run build` sets `KEYSTATIC_ADMIN=0`, so the Keystatic + React
  integrations and the SSR `/keystatic` routes are skipped. The deployed site is a
  pure static export (GitHub Pages). Keep it that way.
- **Hosted admin:** `npm run build:admin` (`ADMIN_HOST=netlify`) builds the same app
  with the admin as SSR routes behind the Netlify adapter, so a non-technical editor
  edits from a browser and Save commits to the repo. Storage auto-selects in
  [keystatic.config.ts](keystatic.config.ts) via `import.meta.env.DEV`: `local` under
  `astro dev`, `github` for any build. (Use `import.meta.env.DEV`, not `process.env` —
  the config is bundled into the browser admin, where a `process.env` check is
  undefined and would wrongly fall back to local.) Setup:
  [docs/hosted-admin.md](docs/hosted-admin.md). The adapter belongs to this build
  only; never let it leak into the public `npm run build`.

## Content guardrails (from the brief)

- This is Quentin's **personal** site; it does not speak for any employer. Walmart may
  be named in body copy, and public work Quentin himself has posted publicly (e.g. his
  own NYC pop-up-shop video) may be shown and named at the owner's discretion. What
  stays out regardless: internal, unreleased, or confidential work, and any implied
  official endorsement. When describing enterprise engagements in the abstract, still
  prefer generic framing ("a Fortune 1 retailer"). Do not present him as an official
  representative in metadata or structured data: machine-readable employer claims
  (`worksFor`, an employer name inside `<head>`) are out. `tools/seo_check.py` fails if
  a flagged company name appears in any page `<head>`, so keep such terms in body
  content only (never in a `seo.*` field, since those render into `<head>`).
- "Don't just wear clothes, wear confidence" survives only as a secondary tagline
  (the footer), not the headline.

## Images: the slot system

Photos are `<img src="assets/img/…">` whose paths are edited as content fields. If a
file is missing, the tag falls back to a labeled placeholder (`onerror` + CSS), so the
layout never breaks. Real files live in `public/assets/img/`. When you add or rename a
slot, update [ASSETS.md](ASSETS.md) so the manifest stays in sync. Bulk-download
originals with `python3 tools/fetch_site_images.py`.

Work-page galleries are data-driven from the `galleries` singleton
(`content/galleries.yaml`) and mirror the old site's portfolio structure:
each set is a **category** (`key`, `title`) holding **photo shoots**
(`slug`, `title`), and each shoot holds its own ordered `images` list, whose first
image is the shoot's thumbnail in the lightbox category view. Work cases reference a
category via `gallery`; archive items also set `shoot` to deep-link into one shoot.
`work.astro` emits the `<script id="gallery-data">` JSON the lightbox reads, and the
lightbox keeps prev/next navigation inside the open shoot. Keep the referenced
category keys and shoot slugs in sync with the YAML (CI checks the keys). Never merge
shoots from different categories into one set: Celebrity men and Celebrity women are
separate categories, as they were on the old site.

## SEO layer

The full technical-SEO layer is generated in code, not authored per page, so it stays
consistent. Editable per page: `seo.title`, `seo.description`, `seo.ogTitle`,
`seo.ogDescription`, `seo.ogType`. Generated by
[src/layouts/BaseLayout.astro](src/layouts/BaseLayout.astro) and
[src/lib/jsonld.ts](src/lib/jsonld.ts):

- **Per page:** canonical + `og:url` (from the page path), the full Open Graph +
  Twitter Card set, `robots`, `theme-color`, and favicon / apple-touch-icon / manifest
  / stylesheet links.
- **Structured data:** a JSON-LD block per page, all keyed to one shared Person entity
  `@id` `https://quentinfears.com/#person` (`WebSite` + `Person` + `WebPage` on home;
  `ProfilePage`, `ContactPage`, `CollectionPage`, or `WebPage`, plus a `BreadcrumbList`,
  on the others).
- **Assets & crawl:** `public/assets/img/og-cover.jpg` (1200×630), favicons / PWA
  icons via `public/site.webmanifest`, and `public/robots.txt` → `public/sitemap.xml`.

Everything is keyed to `https://quentinfears.com` as the single source of truth.

## Analytics

The site uses **Google Analytics 4** (`gtag.js`, stream `Quentin Fears`,
measurement ID `G-1WEVVZN8TV`). This is the **one deliberate exception** to the
no-external-scripts rule: an owner-approved third-party tag, wired so it stays
contained.

- **Single source of truth:** `GA_MEASUREMENT_ID` in
  [src/lib/content.ts](src/lib/content.ts). To change the ID, update it there
  *and* `GA_MEASUREMENT_ID` in [tools/seo_check.py](tools/seo_check.py).
- **Emitted by [BaseLayout.astro](src/layouts/BaseLayout.astro), not per page,**
  so every page (current and future) gets the tag automatically. Do not paste
  the snippet into individual pages.
- **Production only.** The tag is gated behind `import.meta.env.PROD`, so
  `npm run build` (and `build:admin`) include it but `npm run dev` does not, and
  local editing never sends hits to the live property.
- **CI enforces it.** `tools/seo_check.py` fails the build if any page ships
  without both halves of the snippet (the `gtag/js?id=…` loader and the
  `gtag('config', …)` call). New pages/layouts must keep analytics wired; do not
  remove or gut the tag. This is the intended behaviour even though it loads a
  CDN script, so do not "fix" it back out to restore the offline guarantee.
- **Lazy-loaded on purpose.** The `gtag.js` library is injected only after the
  page paints (`load` → `requestIdleCallback`), so it stays off the main thread
  during render and the strict `total-blocking-time ≤ 200ms` gate in
  [lighthouserc.json](lighthouserc.json) still passes. The `gtag('config', …)` call
  queues in `dataLayer` immediately and fires when the library arrives, so no
  pageview is lost. Do not "simplify" this back to an eager `<script async src>` in
  `<head>`: that puts the third-party cost on the main thread during render and can
  fail the TBT gate.
- **Perf budget accepts GA's cost.** The owner accepts the small performance hit
  analytics brings, so `categories:performance` and `largest-contentful-paint` in
  [lighthouserc.json](lighthouserc.json) are **warnings**, not errors (they also
  swing widely on shared CI runners, so they were noisy gates anyway). The
  deterministic gates stay hard errors: `seo = 1.0`, `accessibility ≥ 0.95`,
  `best-practices ≥ 0.95` (still guards third-party/cookie issues), `CLS ≤ 0.05`,
  `TBT ≤ 200ms`, and the image audits. Keep it that way.
- Pages still render and stay legible if the GA request is blocked (no dependency),
  so the offline-friendly experience holds.

## Newsletter

Email capture and a monthly draft, on **Loops** (free plan). The signup box and the
privacy note ship together: never one without the other.

- **Signup box = a plain HTML form, no third-party JS.** This is why Loops was
  chosen over every provider that wants a JS embed: it accepts a plain form POST to a
  "custom form" endpoint, so it keeps the no-external-scripts rule (GA stays the one
  exception). [Newsletter.astro](src/components/Newsletter.astro) posts to
  `settings.newsletter.formEndpoint`; with JS off it is a normal full-page POST, and
  [main.js](public/assets/js/main.js) enhances it to an inline AJAX submit (mirrors
  the contact form, same `_honey` honeypot). Every string, and the endpoint, live in
  the `newsletter` object of [content/settings.yaml](content/settings.yaml) (schema in
  [keystatic.config.ts](keystatic.config.ts)), editable from `/keystatic`. Do **not**
  hardcode the endpoint or paste a Loops JS snippet.
- **Placement is one setting.** `settings.newsletter.placement` is `footer` (the band
  above the footer, every page) or `ideas` (one block on the Ideas page). The Footer
  and Ideas page each render `Newsletter` only for their mode.
- **Double opt-in is on in Loops** (Settings → Sending). It applies only to the form
  endpoint, so subscribers land unconfirmed until they click the email. Never add
  contacts through the API and assume they are confirmed.
- **Privacy + consent are load-bearing, not decoration.** [privacy.astro](src/pages/privacy.astro)
  (`content/privacy.yaml`) is the plain-English note; the consent line next to every
  email field links to it, and so does the contact form. `tools/validate_site.py`
  fails CI if a built newsletter form's action drifts from `settings.yaml`, if the
  honeypot is dropped, or if any page with an email input stops linking the privacy
  note. That triad is what stops a redesign from quietly breaking subscriptions or
  dropping consent. Keep it.
- **CAN-SPAM address:** the physical mailing address required in the email footer is
  set in **Loops account settings**, never in this repo. Do not commit a home address.

### The monthly draft (never a send)

[tools/newsletter_draft.py](tools/newsletter_draft.py), run monthly by
[.github/workflows/newsletter.yml](.github/workflows/newsletter.yml), assembles a
draft and creates it in Loops via `POST /v1/campaigns`. **It never sends.** A human
opens Loops and hits send; silence is not approval.

- The email leads with one styling idea (drawn from `content/ideas.yaml` notes, his
  own words, rotated by month), then a short "what's new" built from
  `instagram-ledger.json` and the git history of `content/*.yaml` (adds and
  replacements; trims are not announced). Window is the previous calendar month.
- **No news, no draft.** `build_draft` returns `None` when the month has nothing to
  report, and the workflow opens no issue. A padded newsletter is worse than none.
- The Loops API key is the `LOOPS_API_KEY` GitHub Actions secret. It never enters the
  repo, the build, client code, a log, or a PR. `--dry-run` renders to
  `newsletter-preview.txt` (gitignored) without touching the API.
- Tests: `python3 tools/test_newsletter_draft.py` (in CI). The pure assembly logic is
  dependency-free; only the CLI edges read YAML, shell out to git, and call Loops.
- One caveat verified on first run: no Loops page states the Campaign API is on by
  default for a new free team, so the first real call is the test. `create_loops_draft`
  is the single place to adjust the request body if the live API differs from the docs.

### When you add a new page

1. Add a singleton to `keystatic.config.ts` (reuse the `seo()` helper) and a
   `content/<page>.yaml` with its copy.
2. Add `src/pages/<page>.astro`: read the singleton and render its sections, wrapped
   in `BaseLayout` with `pagePath="<page>"` (extensionless), the `seo.*` props, a `navCurrent`,
   and a `jsonLd` graph (use `personMinimal` + `breadcrumb` from `src/lib/jsonld.ts`).
   `BaseLayout` supplies the rest of the `<head>` — do not hand-write it.
3. Use exactly one `<h1>` and give every `<img>` an `alt`.
4. Add the page's URL to [public/sitemap.xml](public/sitemap.xml).
5. Run `npm run build && npm run validate` and fix anything reported.

### When the domain changes

`https://quentinfears.com` is the single source of truth. Update `SITE_ORIGIN` in
[src/lib/content.ts](src/lib/content.ts), `BASE` in
[tools/seo_check.py](tools/seo_check.py), and find-and-replace the domain in
`public/robots.txt`, `public/sitemap.xml`, and `public/CNAME` (the Pages custom-domain
pin, served verbatim as `dist/CNAME`). The public site is `https://quentinfears.com`;
GitHub Pages publishes it at `https://qafears.github.io/website/` (the publish URL), and
the canonical/`og:` URLs intentionally point at `quentinfears.com`.

### Indexing

The password gate that guarded the private preview has been removed; the site is
public and `BaseLayout` emits
`robots: index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1`
on every page. `tools/seo_check.py` warns if a gated page is left indexable, or an
ungated page is left `noindex`, so if a gate ever returns, indexing must be turned
off with it.

## Keep things in sync

Two dependency-free validators guard the repo; they read the build output. Run
`npm run build` first (or `npm run check`, which does both), and CI
(`.github/workflows/ci.yml`) builds then runs both on every push and PR:

- `python3 tools/validate_site.py [dir]` — internal links and anchors resolve, gallery
  keys match their JSON, no template junk, and no em dashes (literal or entity) in any
  shipped text file. Reports unfilled `assets/img/` slots as INFO.
- `python3 tools/seo_check.py [dir]` — the SEO invariants (one `<title>`, meta
  description, canonical, required `og:*`/`name` meta, `og:image` resolves, favicon /
  manifest / stylesheet links, one `<h1>`, `alt` on every `<img>`, valid JSON-LD keyed
  to the canonical origin, sitemap membership, gate ↔ indexing coupling, the Google
  Analytics tag on every page, and no employer name in `<head>`), plus `robots.txt` →
  sitemap and manifest/asset existence.

Both default to `dist/` when it exists (else the repo root). CI passes `dist`
explicitly.

The README hero (`docs/preview.jpg`) is a rendered screenshot of the home page.
Regenerate it when the hero changes: serve the build, screenshot the top of the
home page, then re-optimize (JPEG, ~2400px wide).

## Run & deploy

- Preview locally: `npm run dev` (site at http://localhost:4321, admin at
  `/keystatic`). Or `npm run build && npm run preview` for the production build.
- Deploy: pushing to `main` builds and publishes `dist/` to GitHub Pages via
  `.github/workflows/deploy.yml`. The public site is https://quentinfears.com; GitHub
  Pages serves it at https://qafears.github.io/website/ (the publish URL, not the front door).

## Weekly routine: curate the site from new @mrqfears Instagram content

Operating procedure for a recurring weekly agent that keeps the site current with
Quentin's Instagram (@mrqfears). **The site is a curated portfolio, not a feed.**
The weekly run is an editorial pass over the whole site with the new material in
hand — not an ingest job. Nothing gets in just because it is new; new work competes
with what is already there, and the run is as much about replacing and trimming as
adding. Ship mode is auto-merge to live for content edits: content lives in
Keystatic collections under `content/*.yaml`, and merging to `main` builds and
deploys, so the routine edits the YAML directly and lands it through a pull request it
validates and merges itself. ("Auto-merge" means you open the PR and merge your own
green PR without a human approval step, not that you push straight to `main`: `main`
is protected and takes changes only through a PR.)
`instagram-ledger.json` (repo root) is the source of truth for what has already
been considered; never process the same post twice.

Instagram tooling in `tools/` (stdlib-only except the authed one):

- `instagram_new_since.py` — login-free detector (Instagram's public logged-out
  endpoint; no cookies, no Keychain, safe to run unattended). Lists posts newer than
  the ledger. This is the only fetch the unattended routine uses.
- `fetch_instagram_images.py` — login-free fetcher for the recent posts.
- `fetch_instagram_authed.py` — deep gallery-dl backfill; needs the Chrome session
  and a one-time macOS Keychain approval, so it is manual-only.

### Steps

1. **Detect:** `python3 tools/instagram_new_since.py` to list posts newer than the
   ledger. An empty list does not end the run — the critical review in step 3 still
   happens.
2. **Judge** each new post from its caption + image(s) *against what the site
   already shows*. The bar is the site's existing best content, and the default
   verdict is **skip**.

   **Eligibility gate first, quality second.** Only content about Quentin's
   professional creative work is eligible: fashion, styling, editorial and
   campaign imagery, creative leadership, speaking, hosting, and press about that
   work. Anything personal or off-topic — family, friends, relationships, travel,
   food, fitness, humor/memes, politics, faith, celebrations, day-in-the-life —
   is **excluded automatically, before any quality judgment**, no matter how
   polished it looks. When a post mixes both (say, a personal caption on a styled
   photo), it is eligible only if it stands on the professional content alone; if
   the personal part is the point, skip it. For a post that clears the gate,
   route it:
   - **Thought piece** (a style-POV caption, a lesson, a press mention — most recent
     reels are this) → a `{ title, body }` item under `notes.items` in
     `content/ideas.yaml` (title = the hook, body = the idea, lightly edited from the
     caption).
   - **Photoshoot / styled images** → image(s) in `public/assets/img/gallery/`
     and `{ src, cap }` entries in `content/galleries.yaml`, inside the right
     **shoot** of the right **category** (keys: `celebrity-women`, `celebrity-men`,
     `editorial`, `menswear`, `commercial`). A genuinely new shoot gets its own
     `{ slug, title, images }` entry in its category; never append unrelated images
     to an existing shoot. For a headline piece, a case in `content/work.yaml`.
   - **Hosting / on-camera** (Sheen Talk Live, panels, TV) → `content/speak.yaml`.
   - **Off-brand, low-quality, or redundant** → skip (personal/off-topic posts
     never reach this point — they fail the eligibility gate above).

   When the target section is at its budget (below), the incorporation is a
   **replacement**: the new item goes in and the section's weakest item comes out in
   the same commit. Appending past the budget needs a reason recorded in the ledger
   (e.g. a genuinely new body of work opening a new theme).

   **Video (reels)** live in `reels.items` on `content/ideas.yaml` (rendered by the
   vertical player on the Ideas page). Default is *poster + caption + a "Watch on
   Instagram" link* — add the item with `videoSrc` blank, so no video bytes enter the
   repo. To self-host a standout reel instead, fetch its `.mp4`
   (`fetch_instagram_authed.py --videos`), run `python3 tools/prepare_reel.py
   <source.mp4> --name reel-<slug> --caption "…" --permalink "…"` (needs ffmpeg), drop
   the produced files under `public/assets/`, and set `videoSrc`. Self-hosting is a
   deliberate, occasional choice — never auto-host every reel.

   Incorporate only high-confidence, on-brand items; when unsure, skip.
3. **Critical review of the site** — every run, even with zero new posts. Read the
   built site the way a first-time booker would (build it and skim each page's
   rendered content, not just the YAML) and look for cruft:
   - the weakest item in any section this run is adding to — prefer replace over
     grow;
   - stale or dated copy: "recent"/"upcoming" claims that have lapsed, past-tense
     events still framed as future, counts or superlatives the content no longer
     supports;
   - redundancy — two gallery images making the same visual point, two Ideas notes
     circling the same thought; keep the stronger one;
   - anything that reads as filler: an item that would not be missed weakens the
     items around it.
   Trim what fails the review. Removing an image means deleting its YAML entry
   (leave the file in `public/assets/img/`; unreferenced files do not ship weight
   into pages and the image may earn its way back). Shrinking a section below its
   budget is fine when the content is weak.
4. **Prepare assets:** download at full resolution, optimize per `ASSETS.md`
   (gallery squares ~1000×1000, portraits ~1200×1500, < ~300 KB), save as `.jpg`
   under `public/assets/img/…`. Reference them in YAML as `assets/img/…` (the
   public-relative path the site uses).
5. **Edit the YAML** to Keystatic's shape, matching existing entries exactly; keep
   gallery `key`s valid so the lightbox and validators stay in sync.
6. **Update `instagram-ledger.json`:** append every considered post (`shortcode`,
   `date`, `decision` — one of `add` / `replace` / `skip` — `target`, one-line
   `reason`, and for a replace, what came out and why it lost). Site edits from
   step 3 that are not tied to a post go under `trimmed` with the same shape.
   Advance `reviewed_through`.
7. **Publish:** `npm run build`, then `python3 tools/validate_site.py dist` and
   `python3 tools/seo_check.py dist` (same as CI); open a PR, let CI run both
   validators, then merge it to `main` and confirm the Pages deploy succeeds. The commit message summarizes adds, replacements, and
   trims so the week's editorial decisions are auditable at a glance.

### Section budgets

Steady-state sizes — the signal to replace rather than append. These are ceilings
for unattended growth, not targets to fill:

- Gallery categories (`content/galleries.yaml`): **8 images each**, across that
  category's shoots
- Ideas notes (`content/ideas.yaml` `notes.items`): **4–6** · Ideas reels
  (`reels.items`): **3–4**
- Work cases (`content/work.yaml`): **4** · styling archive: **8**

### Guardrails

- **≤ 3 content changes per run** (adds + replacements + trims combined). The bias
  is toward doing less: a run that changes nothing is a valid outcome, not a
  failure.
- **Content only auto-merges.** YAML edits and optimized images go in through a PR you
  validate and merge yourself (no human approval needed for on-brand content); `main`
  is protected, so there is never a direct push. Anything structural — a new page or
  section, removing a whole case study,
  layout/code/CSS changes, reworking a page's story — is out of scope for the
  unattended run: open a PR describing the proposal instead, and say why, so a human
  decides.
- On-brand and professional only; honor the personal-site / no-employer and
  no-confidential-work rules above, and keep the house voice (editorial tone, all-caps
  labels, and no em dashes — restructure the sentence instead). No private individuals
  without clear professional context.
- Idempotent via the ledger. Prefer skipping when unsure — a weekly cadence makes a
  miss harmless, and a skipped post can still be incorporated by a later run if it
  keeps mattering.
- Optimize every image. Do not run `fetch_instagram_authed.py` in the unattended
  routine — its Keychain prompt needs a human at the Mac.

## What not to do

Quick guardrail recap; the reasoning is in the sections above.

- No external fonts, scripts, or CDNs (breaks the offline / CSP guarantee). Build-time deps are fine. The one sanctioned exception is Google Analytics (see "Analytics"); do not add others, and do not remove GA to "restore" the offline rule.
- No root-absolute internal links or assets; keep them relative.
- No em dashes in anything shipped to `dist/`; restructure instead. CI fails on them.
- Do not hand-write or desync the `<head>`, JSON-LD, or sitemap; `BaseLayout` generates them.
- No employer claim in metadata or any `seo.*` field.
- Keep the public `npm run build` static and adapter-free; the Netlify adapter belongs only to `build:admin`.
- Move or rename the crawl files or validators only alongside `tools/*.py` and `.github/workflows/` updates.
