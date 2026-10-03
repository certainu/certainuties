# CERTAINU automated prediction site

This package converts the CERTAINUTIES section into a data-driven feed. `index.html` loads `data/predictions.json`; `scripts/update_predictions.py` refreshes Polymarket market probabilities, resolves finished calls, recalculates the public scorecard in the browser, and selectively locks new calls; GitHub Actions runs the updater every two hours at :17.

## Deploy
1. Put the contents of this folder at the root of a GitHub repository.
2. In GitHub, enable Actions and give workflows read/write repository permission if your repository defaults to read-only workflow tokens.
3. Deploy the repository with GitHub Pages, Cloudflare Pages, Netlify, Vercel, or another static host. Do not open `index.html` directly with `file://`; browsers commonly block local `fetch()` of `data/predictions.json`.
4. Run **Actions → Update CERTAINU Predictions → Run workflow** once. After that the schedule runs every two hours.

## Prediction rules
The included `rules-v1` model is deliberately transparent and conservative. It uses the Polymarket YES probability as a baseline, market volume, a bounded adjustment, and a deterministic question tilt. A new call is locked only when the estimated edge is at least 10 percentage points, volume is at least $25,000, fewer than 5 calls are open, and the market is not already tracked. It creates at most one new call per run. Once locked, the original pick, confidence, and market probability at lock are never rewritten.

Environment variables: `CERTAINU_MIN_VOLUME`, `CERTAINU_MIN_EDGE`, `CERTAINU_MAX_OPEN`, `CERTAINU_MAX_NEW_PER_RUN`.

## Important
This is an entertainment/experimental forecasting system, not financial advice. Before launch, verify the Polymarket fields against the current API behavior and test resolution handling on several completed markets. Add the official wallet to `data/predictions.json` when available.
