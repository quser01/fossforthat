# FossForThat

Open-source & self-hosted swaps for every paid AI tool

Static directory of open-source / self-hosted alternatives to paid AI tools.

Live (GitHub Pages): https://quser01.github.io/fossforthat/

## Local preview

```bash
python3 -m http.server 8765
# open http://127.0.0.1:8765/
```

## Refresh GitHub stats

```bash
./scripts/refresh.sh
# or: node scripts/refresh.js
python3 scripts/build.py
```

## Build

```bash
python3 scripts/build.py
```

## Notes

- Install difficulty = our estimate
- “What you lose” = our assessment
- Stars / license / last commit from public GitHub API (see `data/alternatives.json` → `stats_fetched_at`)
- Editorial overrides: list field names in an alternative's `locked_fields` (e.g. `["license"]`) and the refresh scripts will never overwrite them; `locked_reason` says why
- Newsletter & submit are **coming soon** placeholders (not working forms)
- Do not invent prices on the sponsor page
