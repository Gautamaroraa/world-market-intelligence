# World Market Intelligence

A GitHub-only, evidence-led market research and portfolio decision dashboard.
It separates short-term signals from long-term investment scores, timestamps
research evidence, maps global events to Indian securities, and publishes a
responsive dashboard through GitHub Pages.

## What is working

- Premium responsive dashboard with portfolio, regime, signals and evidence
- Separate short- and long-term decision tables
- Transparent deterministic scoring rules
- GDELT global-event discovery using the standard library only
- Atomic JSON research store committed by GitHub Actions
- Scheduled research every three hours
- Automatic GitHub Pages deployment
- Offline data validation and unit tests
- Safe seed dataset so the interface works before integrations are configured

The included securities and decisions are demonstration data. They are not
current recommendations or investment advice.

## Repository map

```text
app/                     Dashboard interface
public/data/             Versioned dashboard research data
pipelines/collectors/    Read-only external data collectors
pipelines/engine/        Auditable scoring rules
pipelines/run_research.py
tests/                   Scoring tests
.github/workflows/       Research schedule and Pages deployment
```

## Run locally

Requirements: Node.js 22+, npm and Python 3.12+.

```bash
npm ci
npm run dev
```

Validate the research data and scoring engine:

```bash
python -m pipelines.validate_data
python -m unittest discover -s tests
python -m pipelines.run_research --offline
```

Run a live GDELT discovery cycle:

```bash
python -m pipelines.run_research
```

## Deploy using only GitHub

1. Create a private GitHub repository and push this project to its `main`
   branch.
2. Open **Settings → Pages** and choose **GitHub Actions** as the source.
3. Run **Deploy dashboard to GitHub Pages** from the Actions tab.
4. Run **Scheduled market research** once manually to verify collection.

The Pages workflow sets the repository base path automatically. The research
workflow safely exits without changing the dashboard if a source is temporarily
unavailable.

## Secrets

GDELT does not need a key. Future market-data and AI integrations belong in
**Settings → Secrets and variables → Actions**. Never commit credentials.

Suggested secret names are documented in `.env.example`.

## Research integrity

Read `DATA_POLICY.md` before extending collectors or scoring. GDELT discovers
events; it does not independently verify every article. A signal should become
actionable only after primary-source verification or independent corroboration.

## Next production modules

- NSE filing collector and announcement parser
- Zerodha historical and live market-data adapter
- Point-in-time fundamentals store
- Evidence clustering and entity-resolution graph
- Walk-forward backtesting with transaction costs
- Paper portfolio ledger and risk-budget enforcement
