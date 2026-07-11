import { SITE_ORIGIN } from './content';

// Structured-data helpers. JSON-LD is technical SEO, not editor content, so it
// lives in code and stays keyed to the canonical origin (tools/seo_check.py
// requires each block to be valid JSON referencing this origin).
const O = SITE_ORIGIN;

export const PERSON_ID = `${O}/#person`;
export const WEBSITE_ID = `${O}/#website`;

/** The minimal Person node used on subpages. */
export function personMinimal(extra: Record<string, unknown> = {}) {
  return { '@type': 'Person', '@id': PERSON_ID, name: 'Quentin Fears', url: `${O}/`, ...extra };
}

export function breadcrumb(items: { name: string; item: string }[]) {
  return {
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      item: it.item,
    })),
  };
}
