import { createReader } from '@keystatic/core/reader';
import keystaticConfig from '../../keystatic.config';

// Single shared reader over the local content/ files. Runs at build time only;
// no server or database. process.cwd() is the project root during astro build.
export const reader = createReader(process.cwd(), keystaticConfig);

// Canonical origin, the single source of truth for absolute SEO URLs. Keep in
// sync with tools/seo_check.py (BASE), robots.txt, and sitemap.xml.
export const SITE_ORIGIN = 'https://quentinfears.com';
export const OG_IMAGE = `${SITE_ORIGIN}/assets/img/og-cover.jpg`;

// Google Analytics 4 measurement ID. This is the one deliberate exception to
// the "no external scripts/CDN" rule: BaseLayout loads gtag.js from Google on
// production builds only (import.meta.env.PROD), so `npm run dev` never sends
// hits. tools/seo_check.py (GA_MEASUREMENT_ID) enforces that every built page
// carries this tag. Keep the two IDs in sync.
export const GA_MEASUREMENT_ID = 'G-1WEVVZN8TV';
