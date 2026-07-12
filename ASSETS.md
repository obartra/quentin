# Image & media manifest

> **Status (updated):** The slots below are now filled with real images pulled
> from the live site via `tools/fetch_site_images.py`, selected by vision, and
> optimized for web (in `assets/img/`, ~3 MB total). The full 88-image source
> dump lives on the **`site-images`** branch under `assets/img/site-dump/` (it's
> git-ignored on `main`) if you want to swap any choice — every file maps back to
> a page in that branch's `manifest.json`.
>
> **Videos:** the site's videos are hosted on **YouTube** (his Sheen Talk Live
> show *The Journey*). They're embedded, not downloaded — the Speak page plays
> them via click-to-load iframes and links the episodes:
> Larry Sims `WR8hbFuHeqg`, Angela Robinson `7EeeYig__4o`, Tanisha Long `LtZsCVGCOaI`.
> To reuse elsewhere, embed `https://www.youtube-nocookie.com/embed/<id>`.
>
> **Instagram reels** appear on the **Ideas** page (`reels.items` in
> `content/ideas.yaml`). Each is either a poster + caption that links to Instagram
> (the default — no video bytes stored) or a self-hosted `<video>` at
> `public/assets/video/reel-*.mp4` with a poster at `public/assets/img/reel-*.jpg`.
> Produce the self-hosted pair with `python3 tools/prepare_reel.py <source.mp4>
> --name reel-<slug> …` (compact H.264, ~1-2 MB each). Both play via a CSP-safe
> click-to-load — no external embed script.
>
> To change any image: drop a replacement at the same path in `assets/img/` (or
> pick a different file from the `site-images` branch) and it appears — no code
> change needed.


Every image on the site is a real `<img>` tag pointing at `assets/img/`. Until a
file exists, the tag removes itself and a **tasteful labeled placeholder** shows in
its place (the label describes exactly what belongs there). Drop a correctly-named
file in and it appears automatically — no code change required.

**Grab everything from the live site automatically:** run
`python3 tools/fetch_site_images.py` on your own machine (it needs to reach the
site). It crawls quentinfears.com, downloads every image at full Wix resolution
into `assets/img/site-dump/`, writes a `manifest.json`, and — by default —
pushes the dump to a `site-images` branch so Claude can pull it in, view the
images, and place the good ones. Then just say: "the images are on branch
site-images". Add `--no-push` to only download.

Reuse the existing photography from the current quentinfears.com portfolio and the
@mrqfears Instagram grid wherever possible. The one net-new shoot worth commissioning
is **new portraits of Quentin in "leader mode"** — speaking, directing, on set giving
direction — since the current site shows almost everyone except him in that role.

## Recommended specs
- **Format:** `.jpg` (photos) or `.webp`. Keep filenames exactly as listed below.
- **Portraits:** ~1200×1500 (4:5). **Wide/case:** ~1600×1000 (16:10). **Archive squares:** ~1000×1000. **Reel poster:** ~1920×1080 (16:9).
- Compress to < ~300 KB each; the layout is dark, so favor rich, high-contrast images.

## Slots

| File | Page | What to use |
|---|---|---|
| `assets/img/hero-portrait.jpg` | Home hero | **Filled** — current studio headshot (smile, glasses, striped knit, wood backdrop; IG 3432270796993228309). The single most important image. |
| `assets/img/speak-still.jpg` | Home (speak teaser) | On-camera still from Sheen Talk Live / BNC / Hilfiger footage. |
| `assets/img/work-enterprise.jpg` | Work — case 01 | A generic, non-confidential retail/campaign visual (no unreleased Walmart work). |
| `assets/img/work-time.jpg` | Work — case 02 | The TIME feature screenshot or a related office-dressing image. |
| `assets/img/work-editorial.jpg` | Work — case 03 | A strong Glitter/Ladygunn editorial spread he art-directed. |
| `assets/img/work-celebrity.jpg` | Work — case 04 | A standout red-carpet or Sheen cover look. |
| `assets/img/archive-macygray.jpg` | Work — archive | Existing Macy Gray styling photo. |
| `assets/img/archive-skaijackson.jpg` | Work — archive | Existing Skai Jackson styling photo. |
| `assets/img/archive-normanreedus.jpg` | Work — archive | Existing Norman Reedus styling photo. |
| `assets/img/archive-garcelle.jpg` | Work — archive | Existing Garcelle Beauvais styling photo. |
| `assets/img/archive-keeshasharp.jpg` | Work — archive | Existing Keesha Sharp styling photo. |
| `assets/img/archive-ejjohnson.jpg` | Work — archive | Existing EJ Johnson styling photo. |
| `assets/img/archive-sheen.jpg` | Work — archive | Sheen cover story image. |
| `assets/img/archive-ladygunn.jpg` | Work — archive | Ladygunn editorial image. |
| `assets/img/idea-time.jpg` | Ideas | Portrait or TIME feature visual. |
| `assets/img/speak-reel.jpg` | Speak | Poster frame for the speaking reel. |
| `assets/img/speak-stage.jpg` | Speak (`stage` section) | Quentin speaking on stage (100 Black Men of America conference). |
| `assets/img/media-bnc.jpg` | Speak (`media` credits) | Still from the BNC holiday-shopping segment with Marcel Clarke (16:9). |
| `assets/img/media-cali.jpg` | Speak (`media` credits) | Still from the California Live fashion-trends segment (16:9). |
| `assets/img/media-glamour.jpg` | Speak (`media` credits) | Poster frame for Glamour's styling competition *Dress to Kill* (16:9). Source video: https://www.youtube.com/watch?v=_KzZ2pqT_6g |
| `assets/img/about-portrait.jpg` | About | A strong editorial portrait of Quentin. |

## Video — the speaking reel
The Speak page has a play-button poster linking to `contact.html` as a placeholder.
Replace it with the real two-minute reel cut from the **Tommy Hilfiger interview**,
**Sheen Talk Live (_The Journey_)**, and **Black News Channel** footage. Either:
1. Swap the `<a class="reel">` for a `<video>`/`<iframe>` embed in `speak.html`, or
2. Point the link at a hosted reel (YouTube/Vimeo).

## Testimonials — verify before launch
The three testimonial quotes on the Home page (Santana Dempsey, Brian S., and the
Thumbtack review) are drawn from the existing testimonials but should be replaced with
the **exact verbatim wording** from the current Press & Testimonials page before launch.
They're flagged with an HTML comment in `index.html`.

## Contact form endpoint
`contact.html`'s form submits through **FormSubmit** (`formsubmit.co`) — no account or
API key. Submissions are emailed to the address in the form's `action`
(`https://formsubmit.co/hello@quentinfears.com`); change that email to route anywhere.

- **One-time activation:** the FIRST real submission triggers a confirmation email to
  that address — click its link once and the form is live. Until then FormSubmit holds
  submissions.
- JS (`assets/js/main.js`) posts to the `/ajax/` endpoint and shows an inline success or
  error message; with JavaScript off, the form does a normal POST to the same endpoint.
- A hidden `_honey` honeypot filters bots; `_subject` is set to include the inquiry type.
- Alternatives if you'd rather: swap the `action` to a **Formspree** endpoint (same fetch
  works), point it at a **Google Form** `formResponse` URL, or — if you ever host on
  **Netlify** instead of GitHub Pages — add `data-netlify="true"` + a hidden `form-name`
  and Netlify captures it natively (JS auto-detects a non-FormSubmit action and lets it
  POST normally).
