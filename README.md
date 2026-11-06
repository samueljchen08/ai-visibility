# AI-search visibility audit: Out of the Woods Construction & Cabinetry

How often ChatGPT-style answer engines name Out of the Woods (Waltham, MA) when a
homeowner asks for a remodeler in the towns it serves, why they don't, and what to change.

## Reports

| File | What it is |
|---|---|
| `report/report.pdf` | **Two-page brief for Dave.** Current visibility by key area, the six changes, projected visibility after each wave, and a checklist. |
| `report/brief-4page.pdf` | Earlier four-page executive brief. |
| `report/report-full.pdf` | Full report: every query, answer, source, site audit, competitor profiles, methodology. |

Baseline measured 2026-10-28: 0 of 48 service-and-town answers named the firm; 3 of 3 brand-name searches did.

## Pipeline

```
python3 scripts/build_queries.py     # queries.json (40 queries: 5 services x 12 towns x 4 intents)
python3 scripts/make_batches.py      # results/simulated/batch-N.prompt.md for the answer-engine agents
python3 scripts/site_audit.py        # results/audit/site.json
python3 scripts/aggregate.py         # report/summary.json + report/report-full.md
python3 scripts/project.py           # report/projection.json (visibility after each wave of changes)
python3 scripts/twopager.py          # report/report.html + report/report.pdf (needs Google Chrome)
python3 scripts/brief.py             # report/brief-4page.pdf
python3 scripts/render.py            # report/report-full.pdf
```

Real-engine captures (Google AI Mode, Perplexity, ChatGPT) live in `results/real/` and were
recorded from a browser; see `report/narrative/methodology_notes.md`.

## Tests

```
uv run --with pytest --with markdown --python 3.12 python -m pytest -q
```

## Re-measuring after the changes

Re-run the same 40 queries (dispatch `results/simulated/batch-N.prompt.md` to the answer-engine
agents, then `aggregate.py`, `project.py`, `twopager.py`) and compare the mention rate to the
baseline of 0 of 48. The projection in `report/projection.json` is the number to beat.
