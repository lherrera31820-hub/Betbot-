# Betbot-

Sports-betting web app deployed to GitHub Pages with a fully automated,
self-healing CI/CD + monitoring pipeline.

- **Live site:** published by GitHub Actions (URL saved to `PAGES_URL.txt` after setup)
- **Dashboard:** `/dashboard/` on the live site

## Deployment & Monitoring

### How the Pages deployment works

Every push to `main` (and manual `workflow_dispatch` runs) triggers
[`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml):

1. **Build job** — checks out the repo, assembles the static site into `_site/`
   (this is a plain static site, so there is no `npm`/build step), ensures the
   dashboard is present at `_site/dashboard/index.html`, then runs
   `actions/configure-pages@v5` and uploads the folder with
   `actions/upload-pages-artifact@v3`.
2. **Deploy job** — depends on the build, deploys the artifact with
   `actions/deploy-pages@v4` into the `github-pages` environment, and writes a
   run summary (status + live URL) to the job summary.

The workflow declares `contents: read`, `pages: write`, `id-token: write`
permissions and uses a `pages` concurrency group (`cancel-in-progress: false`)
so deployments never overlap.

> If the app later gains a build step (e.g. a `package.json` with a `build`
> script), swap the "Prepare artifact directory" step for a Node setup +
> `npm ci && npm run build` and point the upload path at the build output
> (`./dist` or `./build`).

### One-time repository configuration

Run the idempotent setup script once (requires the `gh` CLI authenticated with
admin rights on the repo):

```bash
./scripts/configure-pages-environment.sh
# or: ./scripts/configure-pages-environment.sh <owner> <repo>
```

It enables Pages with the **GitHub Actions** build type, ensures Actions are
enabled, grants the workflow token read/write permissions, keeps `main` as the
branch fallback, then prints the live URL and saves it to `PAGES_URL.txt`.
Safe to re-run at any time.

### Live dashboard

Visit `/dashboard/` on the deployed site (e.g.
`https://<owner>.github.io/Betbot-/dashboard/`). It is a single dependency-free
HTML file that calls the public GitHub REST API from the browser to show:

- current Pages build status with a colored badge,
- the live site URL,
- the last 10 deployment runs (status, branch, commit, start time, duration,
  and a direct "View logs" link),
- a prominent red banner if the latest run failed or no successful deploy exists.

It auto-refreshes every 60 seconds and shows a "last checked" timestamp.

### Automatic failure alerts

[`.github/workflows/monitor-pages.yml`](.github/workflows/monitor-pages.yml)
watches the pipeline two ways:

- **On every deploy completion** (`workflow_run`): if the deploy did not
  succeed, it opens (or updates) a GitHub Issue labeled **`pages-alert`**
  containing the conclusion, a link to the failed run's logs, the commit SHA,
  and a timestamp. When a later deploy succeeds, it auto-closes the open alert
  with a recovery comment.
- **Every 30 minutes** (`schedule`, a safety net): it verifies Pages is still
  enabled and inspects the latest run. If Pages is misconfigured, the latest run
  failed, or no runs exist despite commits on `main`, it opens/updates the same
  `pages-alert` issue.

Browse active alerts:
[issues labeled `pages-alert`](https://github.com/lherrera31820-hub/Betbot-/issues?q=is%3Aissue+label%3Apages-alert).
