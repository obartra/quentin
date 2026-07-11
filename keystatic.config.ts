import { config, fields, singleton } from '@keystatic/core';

/**
 * Keystatic content model for quentinfears.com.
 *
 * Every editable string, list, and image path on the site lives here as a form
 * field. The Astro pages read this content at build time via the reader API and
 * render it into the exact same markup the site shipped by hand, so the output
 * (and the SEO / validator invariants) stay intact while the words become
 * no-code-editable at /keystatic.
 *
 * Storage selects automatically:
 *   - `astro dev` (local editing): `local` — edits write the content/ files here.
 *   - any build (the hosted admin): `github` — commits straight to the repo via the
 *     GitHub App, which triggers the GitHub Pages deploy. See docs/hosted-admin.md.
 *
 * This uses `import.meta.env.DEV` (not process.env): Vite inlines it into the
 * browser bundle, so the admin UI picks the right mode client-side. A process.env
 * check would be undefined in the browser and always fall back to local.
 */
const storage = import.meta.env.DEV
  ? ({ kind: 'local' } as const)
  : ({ kind: 'github', repo: 'obartra/quentin' } as const);

// --- Reusable field groups ---------------------------------------------------

const seo = () =>
  fields.object(
    {
      title: fields.text({ label: 'Browser / search title', validation: { length: { min: 1 } } }),
      description: fields.text({ label: 'Meta description', multiline: true }),
      ogTitle: fields.text({ label: 'Social share title' }),
      ogDescription: fields.text({ label: 'Social share description', multiline: true }),
      ogType: fields.select({
        label: 'Open Graph type',
        options: [
          { label: 'website', value: 'website' },
          { label: 'profile', value: 'profile' },
          { label: 'article', value: 'article' },
        ],
        defaultValue: 'website',
      }),
    },
    { label: 'SEO & social' }
  );

const cta = () =>
  fields.object(
    {
      heading: fields.text({ label: 'Heading' }),
      body: fields.text({ label: 'Body', multiline: true }),
      buttonLabel: fields.text({ label: 'Button label' }),
      buttonHref: fields.text({ label: 'Button link', description: 'e.g. contact.html' }),
    },
    { label: 'Closing call-to-action' }
  );

// A photo slot. `src` is a path under the site root (e.g.
// assets/img/hero-portrait.jpg); a missing file falls back to the labeled
// placeholder built from `tag` / `label`.
const photo = (label: string) =>
  fields.object(
    {
      src: fields.text({
        label: 'Image path',
        description: 'Path under the site root, e.g. assets/img/hero-portrait.jpg',
      }),
      alt: fields.text({ label: 'Alt text (accessibility)' }),
      tag: fields.text({ label: 'Placeholder tag (shown until the photo is added)' }),
      label: fields.text({ label: 'Placeholder caption' }),
    },
    { label }
  );

const eyebrowHeadingIntro = () =>
  fields.object(
    {
      eyebrow: fields.text({ label: 'Eyebrow' }),
      heading: fields.text({ label: 'Heading', multiline: true }),
      intro: fields.text({ label: 'Intro', multiline: true }),
    },
    { label: 'Section header' }
  );

const textItem = (label = 'Value') => fields.text({ label });

export default config({
  storage,
  ui: {
    brand: { name: 'Quentin Fears — site content' },
    navigation: {
      Pages: ['home', 'work', 'ideas', 'speak', 'about', 'contact'],
      Shared: ['settings', 'galleries'],
    },
  },

  singletons: {
    galleries: singleton({
      label: 'Galleries (lightbox)',
      path: 'content/galleries',
      format: { data: 'yaml' },
      schema: {
        sets: fields.array(
          fields.object({
            key: fields.text({
              label: 'Gallery key',
              description: 'Referenced by Work-page buttons via data-gallery, e.g. editorial',
            }),
            images: fields.array(
              fields.object({
                src: fields.text({ label: 'Image path' }),
                cap: fields.text({ label: 'Caption' }),
              }),
              { label: 'Images', itemLabel: (p) => p.fields.src.value || 'Image' }
            ),
          }),
          { label: 'Galleries', itemLabel: (p) => p.fields.key.value }
        ),
      },
    }),

    settings: singleton({
      label: 'Site settings',
      path: 'content/settings',
      format: { data: 'yaml' },
      schema: {
        email: fields.text({ label: 'Contact email' }),
        instagram: fields.url({ label: 'Instagram URL' }),
        instagramHandle: fields.text({ label: 'Instagram handle', description: 'e.g. @mrqfears' }),
        linkedin: fields.url({ label: 'LinkedIn URL' }),
        footerBlurb: fields.text({ label: 'Footer blurb', multiline: true }),
        tagline: fields.text({ label: 'Footer tagline' }),
        copyrightName: fields.text({ label: 'Copyright name' }),
        copyrightYear: fields.text({ label: 'Copyright year (fallback)' }),
      },
    }),

    home: singleton({
      label: 'Home page',
      path: 'content/home',
      format: { data: 'yaml' },
      schema: {
        seo: seo(),
        hero: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            role: fields.text({ label: 'Role line' }),
            philosophy: fields.text({ label: 'Philosophy paragraph', multiline: true }),
            buttons: fields.array(
              fields.object({
                label: fields.text({ label: 'Label' }),
                href: fields.text({ label: 'Link' }),
                external: fields.checkbox({ label: 'Opens in new tab', defaultValue: false }),
                solid: fields.checkbox({ label: 'Solid (primary) style', defaultValue: false }),
              }),
              { label: 'Buttons', itemLabel: (p) => p.fields.label.value }
            ),
            image: photo('Hero portrait'),
          },
          { label: 'Hero' }
        ),
        proof: fields.array(
          fields.object({
            num: fields.text({ label: 'Number' }),
            title: fields.text({ label: 'Title' }),
            body: fields.text({ label: 'Body', multiline: true }),
          }),
          { label: 'Proof points', itemLabel: (p) => p.fields.title.value }
        ),
        belief: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            quote: fields.text({ label: 'Quote (HTML allowed)', multiline: true }),
            cite: fields.text({ label: 'Attribution' }),
          },
          { label: 'The idea' }
        ),
        selectedWork: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            intro: fields.text({ label: 'Intro', multiline: true }),
            cards: fields.array(
              fields.object({
                tag: fields.text({ label: 'Tag' }),
                title: fields.text({ label: 'Title' }),
                body: fields.text({ label: 'Body', multiline: true }),
                href: fields.text({ label: 'Link' }),
              }),
              { label: 'Cards', itemLabel: (p) => p.fields.title.value }
            ),
            moreLabel: fields.text({ label: 'More link label' }),
            moreHref: fields.text({ label: 'More link target' }),
          },
          { label: 'Selected work' }
        ),
        speakTeaser: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            lead: fields.text({ label: 'Lead', multiline: true }),
            linkLabel: fields.text({ label: 'Link label' }),
            linkHref: fields.text({ label: 'Link target' }),
            image: photo('Reel still'),
          },
          { label: 'Speak teaser' }
        ),
        testimonials: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            items: fields.array(
              fields.object({
                quote: fields.text({ label: 'Quote', multiline: true }),
                name: fields.text({ label: 'Name' }),
                role: fields.text({ label: 'Role' }),
              }),
              { label: 'Quotes', itemLabel: (p) => p.fields.name.value }
            ),
          },
          { label: 'Testimonials' }
        ),
        press: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            logos: fields.array(textItem('Name'), { label: 'Press names', itemLabel: (p) => p.value }),
          },
          { label: 'Press strip' }
        ),
        cta: cta(),
      },
    }),

    work: singleton({
      label: 'Work page',
      path: 'content/work',
      format: { data: 'yaml' },
      schema: {
        seo: seo(),
        hero: eyebrowHeadingIntro(),
        cases: fields.array(
          fields.object({
            tag: fields.text({ label: 'Kicker tag' }),
            title: fields.text({ label: 'Title' }),
            image: photo('Case photo'),
            gallery: fields.text({ label: 'Gallery key to open', description: 'A galleries key, or blank for no button' }),
            meta: fields.array(
              fields.object({
                dt: fields.text({ label: 'Label' }),
                dd: fields.text({ label: 'Value (HTML allowed)', multiline: true }),
              }),
              { label: 'Detail rows', itemLabel: (p) => p.fields.dt.value }
            ),
            footerKind: fields.select({
              label: 'Trailing element',
              options: [
                { label: 'None', value: 'none' },
                { label: 'Attribution note', value: 'note' },
                { label: 'Read-more link', value: 'link' },
              ],
              defaultValue: 'none',
            }),
            footerText: fields.text({ label: 'Note / link text', multiline: true }),
            footerHref: fields.text({ label: 'Link target (for read-more)' }),
          }),
          { label: 'Case studies', itemLabel: (p) => p.fields.title.value }
        ),
        archive: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            intro: fields.text({ label: 'Intro', multiline: true }),
            items: fields.array(
              fields.object({
                src: fields.text({ label: 'Image path' }),
                alt: fields.text({ label: 'Alt text' }),
                gallery: fields.text({ label: 'Gallery key' }),
                capTitle: fields.text({ label: 'Caption title' }),
                capSub: fields.text({ label: 'Caption subtitle' }),
              }),
              { label: 'Archive items', itemLabel: (p) => p.fields.capSub.value || p.fields.alt.value }
            ),
            footnote: fields.text({ label: 'Footnote', multiline: true }),
          },
          { label: 'Styling archive' }
        ),
        cta: cta(),
      },
    }),

    ideas: singleton({
      label: 'Ideas page',
      path: 'content/ideas',
      format: { data: 'yaml' },
      schema: {
        seo: seo(),
        hero: eyebrowHeadingIntro(),
        timeFeature: fields.object(
          {
            image: photo('TIME feature photo'),
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            pullquote: fields.text({ label: 'Pull quote', multiline: true }),
            attribution: fields.text({ label: 'Attribution' }),
            lead: fields.text({ label: 'Lead paragraph', multiline: true }),
          },
          { label: 'TIME feature' }
        ),
        thesis: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            quote: fields.text({ label: 'Quote (HTML allowed)', multiline: true }),
            cite: fields.text({ label: 'Attribution' }),
          },
          { label: 'Recurring thesis' }
        ),
        notes: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            items: fields.array(
              fields.object({
                title: fields.text({ label: 'Title' }),
                body: fields.text({ label: 'Body', multiline: true }),
              }),
              { label: 'Notes', itemLabel: (p) => p.fields.title.value }
            ),
          },
          { label: 'Notes on style' }
        ),
        formats: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            intro: fields.text({ label: 'Intro', multiline: true }),
            items: fields.array(
              fields.object({
                tag: fields.text({ label: 'Tag' }),
                title: fields.text({ label: 'Title' }),
                body: fields.text({ label: 'Body', multiline: true }),
              }),
              { label: 'Formats', itemLabel: (p) => p.fields.title.value }
            ),
          },
          { label: 'Signature formats' }
        ),
        cta: cta(),
      },
    }),

    speak: singleton({
      label: 'Speak page',
      path: 'content/speak',
      format: { data: 'yaml' },
      schema: {
        seo: seo(),
        hero: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            intro: fields.text({ label: 'Intro', multiline: true }),
            buttonLabel: fields.text({ label: 'Button label' }),
          },
          { label: 'Hero' }
        ),
        reel: fields.object(
          {
            youtubeId: fields.text({ label: 'YouTube video id' }),
            ariaLabel: fields.text({ label: 'Accessible label' }),
            image: photo('Reel poster'),
            caption: fields.text({ label: 'Caption', multiline: true }),
          },
          { label: 'Reel' }
        ),
        topics: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            intro: fields.text({ label: 'Intro', multiline: true }),
            items: fields.array(
              fields.object({
                title: fields.text({ label: 'Title' }),
                body: fields.text({ label: 'Body', multiline: true }),
              }),
              { label: 'Talk topics', itemLabel: (p) => p.fields.title.value }
            ),
          },
          { label: 'Talk topics' }
        ),
        formats: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            chips: fields.array(textItem('Format'), { label: 'Format chips', itemLabel: (p) => p.value }),
          },
          { label: 'Formats' }
        ),
        media: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            intro: fields.text({ label: 'Intro', multiline: true }),
            episodes: fields.array(
              fields.object({
                href: fields.text({ label: 'Link' }),
                thumbSrc: fields.text({ label: 'Thumbnail path' }),
                thumbAlt: fields.text({ label: 'Thumbnail alt' }),
                tag: fields.text({ label: 'Tag' }),
                title: fields.text({ label: 'Title' }),
                body: fields.text({ label: 'Body', multiline: true }),
              }),
              { label: 'Episodes', itemLabel: (p) => p.fields.title.value }
            ),
            footnote: fields.text({ label: 'Footnote', multiline: true }),
          },
          { label: 'Media credits' }
        ),
        cta: cta(),
      },
    }),

    about: singleton({
      label: 'About page',
      path: 'content/about',
      format: { data: 'yaml' },
      schema: {
        seo: seo(),
        hero: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading (HTML allowed)', multiline: true }),
            intro: fields.text({ label: 'Intro', multiline: true }),
          },
          { label: 'Hero' }
        ),
        portrait: photo('Portrait'),
        prose: fields.text({
          label: 'Biography (HTML allowed)',
          description: 'The story paragraphs. Simple HTML like <strong>, <em>, <span class="drop"> is supported.',
          multiline: true,
        }),
        arc: fields.object(
          {
            eyebrow: fields.text({ label: 'Eyebrow' }),
            heading: fields.text({ label: 'Heading' }),
            items: fields.array(
              fields.object({
                year: fields.text({ label: 'Marker' }),
                title: fields.text({ label: 'Title' }),
                body: fields.text({ label: 'Body (HTML allowed)', multiline: true }),
              }),
              { label: 'Timeline', itemLabel: (p) => p.fields.title.value }
            ),
          },
          { label: 'The arc (timeline)' }
        ),
        cta: cta(),
      },
    }),

    contact: singleton({
      label: 'Contact page',
      path: 'content/contact',
      format: { data: 'yaml' },
      schema: {
        seo: seo(),
        hero: eyebrowHeadingIntro(),
        inquiries: fields.array(
          fields.object({
            asideTitle: fields.text({ label: 'Aside title' }),
            asideBody: fields.text({ label: 'Aside body', multiline: true }),
            radioValue: fields.text({ label: 'Form value' }),
            radioLabel: fields.text({ label: 'Form label' }),
          }),
          { label: 'Inquiry types', itemLabel: (p) => p.fields.asideTitle.value }
        ),
        directLine: fields.text({
          label: 'Direct line (HTML allowed)',
          description: 'e.g. Prefer to reach me directly? Email <a href="...">...</a>.',
          multiline: true,
        }),
      },
    }),
  },
});
