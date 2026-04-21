# Marketing Performance Ledger

A self-hosted, auto-refreshing marketing dashboard for a multi-studio fitness portfolio. Pulls Facebook, Google Ads, and TikTok data from Windsor.ai, normalises spend to GBP, matches ad accounts to your studios list, and renders a single-file HTML dashboard — all on a daily cron, fully automated via GitHub Actions and Pages.

![Stack](https://img.shields.io/badge/python-3.11-blue) ![Deploy](https://img.shields.io/badge/deploy-GitHub%20Pages-green) ![Data](https://img.shields.io/badge/source-Windsor.ai-orange) ![Refresh](https://img.shields.io/badge/refresh-daily%2006:00%20UTC-purple)

---

## What you get

- **One URL** — `https://<your-username>.github.io/<repo-name>/` — that always shows the latest 30 days of paid media performance
- **Refreshes automatically** every day at 06:00 UTC
- **Filters**: region, country, platform
- **Metrics**: spend (GBP), impressions, clicks, CTR, CPM, leads, CPL
- **Sortable per-studio ledger** table
- **Free to run** — GitHub Actions free tier covers this easily (one short workflow per day)

---

## One-time setup (~10 minutes)

### 1. Get your Windsor.ai API key

1. Log in to [onboard.windsor.ai](https://onboard.windsor.ai)
2. Go to **Settings** → **API Access**
3. Copy your API key (keep it private — it grants read access to all your Windsor data)

### 2. Fork or create this repo on GitHub

**Option A — upload this archive directly:**

1. Go to [github.com/new](https://github.com/new), create a new repo (public or private both work for private-repo Pages on paid plans; public is fine for most)
2. Unzip this archive locally
3. In the unzipped folder:
   ```bash
   git init -b main
   git add .
   git commit -m "Initial commit: marketing dashboard scaffold"
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

**Option B — paste files into a fresh repo via the GitHub web UI:**

You can also just create the repo on github.com, then drag-and-drop the unzipped folder contents into the "upload files" area. Works fine for first-push.

### 3. Add your Windsor API key as a repository secret

1. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `WINDSOR_API_KEY`
4. Value: paste your Windsor API key
5. Click **Add secret**

### 4. Enable GitHub Pages

1. In your repo, go to **Settings** → **Pages**
2. Under **Build and deployment** → **Source**, select **GitHub Actions**
3. That's it — the workflow will deploy there automatically

### 5. Trigger the first run

1. Go to the **Actions** tab in your repo
2. Click **Refresh Dashboard** in the left sidebar
3. Click **Run workflow** → **Run workflow** (green button)
4. Wait ~2 minutes for it to finish (green tick = success)
5. Visit `https://<your-username>.github.io/<repo-name>/` — your dashboard is live

From now on, the workflow runs every day at 06:00 UTC. No further action needed.

---

## How it works

```
 GitHub cron (06:00 UTC daily)
          │
          ▼
 refresh.py
          │
          ├── 1. pull from Windsor.ai
          │    · facebook  (7d + 30d in two calls — timeouts at scale)
          │    · google_ads (30d)
          │    · tiktok    (30d)
          │
          ├── 2. build_data.py
          │    · load studios.tsv
          │    · fuzzy-match ad accounts to studios
          │    · normalise spend across currencies to GBP
          │    · emit unified snapshot
          │
          └── 3. build_html.py
               · embed snapshot into HTML template
               · write public/index.html
          │
          ▼
 GitHub Pages
 → https://<username>.github.io/<repo>/
```

### File layout

```
.
├── .github/workflows/
│   └── refresh.yml           GitHub Actions cron + Pages deploy
├── scripts/
│   ├── refresh.py            Top-level orchestrator
│   ├── windsor_client.py     Windsor.ai REST client (retries, auth)
│   ├── build_data.py         Matching + FX normalisation
│   └── build_html.py         HTML template + renderer
├── public/
│   └── index.html            ← Generated on each run. Served by GitHub Pages
├── studios.tsv               Your studios list (edit as needed)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Maintenance

### Updating the studios list

Edit `studios.tsv` (tab-separated: `Studio Name`, `Studio ID`, `Country`, `Region`), commit, push. The next scheduled run — or a manual one — will pick it up.

### Adjusting FX rates

Rates are held constant for each snapshot period. Edit `FX_TO_GBP` at the top of `scripts/build_data.py` and push. To automate live FX rates, replace that dict with a call to an exchange-rate API — about 20 lines of change.

### Tightening or loosening fuzzy matching

In `scripts/build_data.py`:
- `MATCH_THRESHOLD` (default 0.72) — raise to be stricter, lower to be looser
- `_NOISE_TOKENS` — add brand-specific noise terms your account names include

### Changing the refresh schedule

Edit the cron line in `.github/workflows/refresh.yml`:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'   # Daily at 06:00 UTC
```

Examples: `'0 */6 * * *'` = every 6 hours. `'0 6 * * 1'` = Mondays only at 06:00 UTC. [crontab.guru](https://crontab.guru) is helpful.

### Manually refreshing

Actions tab → **Refresh Dashboard** → **Run workflow** → **Run workflow** button. Takes ~2 minutes.

### Running locally (to test changes)

```bash
pip install -r requirements.txt
WINDSOR_API_KEY=your_key_here python scripts/refresh.py
open public/index.html
```

Or skip the API call entirely and just rebuild from cached raw JSON:

```bash
python scripts/build_data.py     # writes raw/snapshot.json
python scripts/build_html.py     # writes public/index.html
```

---

## Troubleshooting

### The workflow failed with "WINDSOR_API_KEY is not set"

Add the secret at repo **Settings** → **Secrets and variables** → **Actions**. The name must be exactly `WINDSOR_API_KEY`.

### The workflow runs but Pages returns 404

Check **Settings** → **Pages** → **Source** is set to **GitHub Actions** (not "Deploy from a branch"). The deployment can take 1–2 minutes after a workflow run completes.

### The workflow times out on Facebook

The Facebook 30-day query can be slow when you have many ad accounts. The script already splits it (7d + 30d) to avoid this, but if it still times out, options:
- Increase `DEFAULT_TIMEOUT` in `scripts/windsor_client.py`
- Filter accounts: edit the `pull()` call in `refresh.py` to include an `accounts=[...]` list of specific account IDs rather than all

### Dashboard shows an "Unmatched" bucket with significant spend

These are ad accounts whose names don't fuzzy-match any studio in your list. Common causes:
- HQ / franchise-sales / brand-level accounts (legitimately not a single studio)
- A studio missing from `studios.tsv` — add it
- Noise in the ad account name that the normaliser doesn't strip — add tokens to `_NOISE_TOKENS`

Open `public/index.html` and filter by region = "Unmatched" to see the exact accounts involved.

### Lead numbers look low

Leads currently come from Google Ads' `conversions` field only. Facebook and TikTok lead events are available from Windsor but aren't pulled in this setup (adding them is straightforward — add fields to the `pull()` calls in `refresh.py`).

---

## Security notes

- The Windsor API key is stored as an encrypted GitHub secret and is only available to the workflow at runtime. It is never logged.
- The generated dashboard is a static HTML file with aggregated metrics — no raw access tokens are exposed.
- If your repo is **public**, the published dashboard is publicly accessible at the Pages URL. For a private dashboard, use a private repo on a GitHub Team/Enterprise plan, which supports authenticated Pages.

---

## Cost

- **GitHub Actions free tier**: 2,000 minutes/month for public repos, unlimited for private repos on Free plan. A daily run of this workflow takes ~2 minutes — **~60 minutes/month**.
- **GitHub Pages**: free for public repos, included in Team/Enterprise for private.
- **Windsor.ai**: pricing depends on your plan; API calls count toward your existing usage.

Total monthly cost for most setups: **£0**.

---

## What's not included (deliberately)

- **Historical trends** — the dashboard shows last 30 days only. For week-over-week or month-over-month deltas, you'd add a snapshot archive (commit each day's `snapshot.json` to a `history/` dir, read the last N in the HTML template).
- **Live FX rates** — rates are fixed in `build_data.py`. Add an exchange-rate API call to `build()` if you need them daily-accurate.
- **Alerts** — no "if CPL jumps 30% notify Slack" logic. Could be added in `refresh.py` before the HTML render step.
- **Auth on the dashboard** — anyone with the URL can view it (if the repo is public). For internal sharing, use a private repo on a paid GitHub plan.

These are all reasonable next steps if you want them — ask.
