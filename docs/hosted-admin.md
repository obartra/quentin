# Hosted admin (edit content from a browser)

Goal: let a non-technical editor open a URL, sign in with GitHub, edit content in
forms, and hit Save — with no dev server and no command line. Saving commits to the
repo, which triggers the GitHub Pages deploy of the public site.

## How it fits together

```
Editor's browser ──▶ Netlify (SSR) ──▶ /keystatic admin
                                          │  Save
                                          ▼
                        commit to  github.com/obartra/quentin (main)
                                          │
                                          ▼
                   .github/workflows/deploy.yml builds + publishes
                                          ▼
                     GitHub Pages  ── the public, canonical site
```

- **Public site:** unchanged. Static, on GitHub Pages (`npm run build`).
- **Admin:** one small Netlify deploy of the *same* repo, built with
  `npm run build:admin` (already wired in `netlify.toml`). It serves the Keystatic
  admin at `/keystatic` as a serverless function and does nothing else important.
- **Auth + writes:** a GitHub App. Only people with write access to the repo can
  edit. Secrets live in Netlify's env, never in the repo.

Two builds, one project:

| Build              | Command             | Output              | Where        |
| ------------------ | ------------------- | ------------------- | ------------ |
| Public site        | `npm run build`     | static `dist/`      | GitHub Pages |
| Hosted admin       | `npm run build:admin` | static + SSR function | Netlify     |

## One-time setup (about 15 minutes)

### 1. Create the Netlify site

1. Netlify → **Add new site → Import an existing project** → pick
   `obartra/quentin`.
2. Netlify reads `netlify.toml`, so the build command (`npm run build:admin`),
   publish dir (`dist`), and Node version are already set. Deploy once. It will
   build but the admin won't authenticate yet — that's expected until step 2.
3. Note the site URL, e.g. `https://quentinfears-admin.netlify.app`.

### 2. Create the Keystatic GitHub App (guided)

Keystatic can create the GitHub App for you:

1. Visit `https://<your-netlify-site>/keystatic` and follow the **"Create GitHub
   App"** prompt. It sends you to GitHub with the correct permissions and callback
   pre-filled.
2. On GitHub, set the callback / homepage to your Netlify URL, create the app, then
   **Install** it on the `obartra/quentin` repository.
3. GitHub shows the app's **Client ID**, a generated **Client secret**, and the app
   **slug**. Keystatic hands these back to paste into Netlify (next step).

If you prefer to create the app by hand, its repository permissions must be
**Contents: Read & write** and **Metadata: Read-only**, and the callback URL is
`https://<your-netlify-site>/api/keystatic/github/oauth/callback`.

### 3. Set Netlify environment variables

Netlify → Site → **Settings → Environment variables**. Add:

| Variable                          | Value                                                      |
| --------------------------------- | --------------------------------------------------------- |
| `KEYSTATIC_GITHUB_CLIENT_ID`      | from the GitHub App                                       |
| `KEYSTATIC_GITHUB_CLIENT_SECRET`  | from the GitHub App                                       |
| `KEYSTATIC_SECRET`                | a random 32-byte hex string (`openssl rand -hex 32`)      |
| `PUBLIC_KEYSTATIC_GITHUB_APP_SLUG`| the GitHub App slug (e.g. `quentinfears-content`)         |

You do **not** need to set a storage variable: the admin auto-selects GitHub storage
for any build (`import.meta.env.DEV` in `keystatic.config.ts`), and `netlify.toml`
already passes `ADMIN_HOST=netlify` via the build command. Redeploy after setting the
variables above.

### 4. Use it

1. Give the editor the URL `https://<your-netlify-site>/keystatic`.
2. They click **Sign in with GitHub** (they must be a collaborator on the repo).
3. They edit any page in forms and hit **Save**. Keystatic commits to `main`.
4. `deploy.yml` rebuilds and publishes the public site to GitHub Pages within a
   couple of minutes.

## Notes

- **The config already points at the repo.** `keystatic.config.ts` uses
  `repo: 'obartra/quentin'` for GitHub storage. Change it if the repo moves.
- **Local editing still works** with no setup: `npm run dev` → `/keystatic` uses
  local file storage and never touches GitHub. Contributors who have the repo checked
  out can use that instead of the hosted admin.
- **Even simpler, if you don't want to run your own GitHub App:** Keystatic Cloud
  (keystatic.cloud, free tier) manages the app for you. Switch `storage` to
  `{ kind: 'cloud' }` and add a `cloud: { project: '<team>/<project>' }` key in
  `keystatic.config.ts`. You still host the admin (Netlify) the same way.
- **Cost:** the GitHub App and GitHub Pages are free. Netlify's free tier easily
  covers a single-editor admin. Nothing here is a paid dependency.
- **Security:** only repo collaborators can sign in and commit. The Netlify URL also
  renders a gated copy of the site; the canonical site remains GitHub Pages. Do not
  put the Netlify secrets in the repo.
