# CLAUDE.md

## Project

quentinfears.com is a static portfolio site for celebrity stylist Quentin Fears.
Plain HTML/CSS/JS (no build step), deployed to **GitHub Pages on every push to
`main`** via `.github/workflows/deploy.yml`. Pages: `index.html` (home),
`work.html` (case studies + archive grid), `ideas.html` (thought leadership),
`speak.html` (hosting), `about.html`, `contact.html`. Images live flat in
`assets/img/`; slot names and web-optimization specs are documented in
`ASSETS.md`. Every `<img>` uses `loading="lazy"` and `onerror="this.remove()"`.

Tools in `tools/`: `fetch_site_images.py` (old-site crawler),
`fetch_instagram_images.py` (login-free recent-posts fetcher),
`fetch_instagram_authed.py` (deep gallery-dl backfill, needs the Chrome session +
a one-time Mac Keychain approval), `instagram_new_since.py` (weekly-routine
detector, below).

---

## Weekly routine: sync the site from new @mrqfears Instagram content

**Status: DRAFT (not yet scheduled).** This is the operating procedure for a
recurring weekly agent that keeps the site fresh with worthwhile new Instagram
content. Ship mode is **auto-merge to live**: a commit to `main` deploys within
minutes, so the routine commits directly to `main`, no PR.

Source of truth for what has already been handled: **`instagram-ledger.json`**
(repo root). Never process the same post twice; the ledger is authoritative.

### Steps

1. **Detect.** Run `python3 tools/instagram_new_since.py`. It reads recent posts
   via Instagram's public logged-out endpoints (no login, no Keychain, safe to
   run unattended) and lists posts newer than the ledger's `reviewed_through`
   marker that are not already in the ledger. If none, stop.

2. **Judge each new post** from its caption and image(s). Classify and route:
   - **Photoshoot / styled images** (editorial, campaign, red carpet, celebrity
     styling, on-set): candidate for the `work.html` **archive grid**.
   - **Thought piece** (a substantive caption on style POV, a lesson, a press
     feature): candidate for `ideas.html` (a short `.note` card, or a featured
     `<figure>` + copy block for longer pieces).
   - **Hosting / on-camera** (Sheen Talk Live, panels, TV): candidate for
     `speak.html`.
   - **Personal, off-brand, low-quality, or redundant**: skip.

   Incorporate only **high-confidence, on-brand** items. When uncertain, skip.
   Cap at **<= 2 incorporations per week** to avoid churn.

3. **Prepare the asset.** Download the chosen image(s) at full resolution (URL is
   in the detector output). Optimize per `ASSETS.md`: archive squares ~1000x1000,
   portraits ~1200x1500, compress to < ~300 KB, save as `.jpg` in `assets/img/`
   with a descriptive slot name (`archive-NN.jpg`, `idea-<slug>.jpg`, ...).

4. **Incorporate**, mirroring existing markup exactly:
   - Photoshoot -> add a `<figure class="ph ph--tall reveal" data-tag="..."
     data-label="..."><img src="assets/img/archive-NN.jpg" alt="..."
     loading="lazy" onerror="this.remove()"><figcaption class="cap"><b>Category</b>
     <span>Label</span></figcaption></figure>` to the `work.html` archive grid.
   - Thought piece -> add a `.note` card (short) or a featured idea block to
     `ideas.html`.
   - Update `ASSETS.md` if a documented slot changes.

5. **Update `instagram-ledger.json`.** For every post considered, append an entry
   (`shortcode`, `date`, `decision`: incorporated | skipped, `target` file, and a
   one-line `reason`). Advance `reviewed_through` to the newest post seen.

6. **Publish.** Commit to `main` with a message summarizing the change, push, and
   confirm the Pages deploy succeeds.

### Guardrails

- On-brand and professional only. No private/personal content, no faces of
  private individuals without clear professional context.
- Honor the "no unreleased/confidential work" note in `ASSETS.md`.
- Idempotent: the ledger prevents reprocessing. Prefer skipping when unsure;
  missing one week is harmless.
- Optimize every image; keep `assets/img/` weight reasonable.
- The detector is login-free and unattended-safe. Do NOT use
  `fetch_instagram_authed.py` in the unattended routine (its Keychain prompt
  needs a human at the Mac); it is for manual deep backfills only.
