// @ts-check
import { defineConfig } from 'astro/config';

// Three build shapes from one project:
//
//  1. Public site  — `npm run build` (KEYSTATIC_ADMIN=0): pure static, no adapter,
//     no admin. Deploys to GitHub Pages. This is the canonical site.
//  2. Local dev    — `npm run dev` (nothing set): admin at /keystatic in local
//     storage mode (edits the content/ files); site pages render normally.
//  3. Hosted admin — `npm run build:admin` (ADMIN_HOST=netlify, KEYSTATIC_STORAGE=
//     github): the same app with the Keystatic admin as SSR routes behind a
//     serverless adapter, so a non-technical editor can edit from a browser. The
//     admin commits to the repo, which triggers the Pages deploy. See
//     docs/hosted-admin.md.
const enableAdmin = process.env.KEYSTATIC_ADMIN !== '0';
const adminHost = process.env.ADMIN_HOST; // 'netlify' builds the hosted admin
const buildingAdmin = Boolean(adminHost);

async function loadAdminIntegrations() {
  const [{ default: react }, { default: keystatic }] = await Promise.all([
    import('@astrojs/react'),
    import('@keystatic/astro'),
  ]);
  return [react(), keystatic()];
}

async function loadAdapter() {
  if (adminHost === 'netlify') {
    const { default: netlify } = await import('@astrojs/netlify');
    return netlify();
  }
  return undefined;
}

// https://astro.build/config
export default defineConfig({
  // Canonical origin. The site is served (pre-launch) from GitHub Pages at a
  // subpath, but every internal link is relative, so it works under both the
  // subpath and the apex domain. `base` stays '/' on purpose.
  site: 'https://quentinfears.com',
  base: '/',
  trailingSlash: 'ignore',
  // Emit flat files (about.html, work.html, ...) to match the hand-authored
  // layout, its canonical/og URLs, the sitemap, and the validators.
  build: { format: 'file' },
  // Output stays static; the site pages are always prerendered. The admin build
  // adds an adapter so Keystatic's own routes (which are prerender:false) run
  // on-demand, while the site pages remain static.
  output: 'static',
  adapter: await loadAdapter(),
  integrations: buildingAdmin || enableAdmin ? await loadAdminIntegrations() : [],
  devToolbar: { enabled: false },
});
