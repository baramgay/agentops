# Example: Data Team Pipeline

This example shows how to run a full data analysis project using agentops' data team agents.

## Scenario

Monthly regional housing report: collect raw transaction data, clean it, run statistics, map it spatially, visualize, and deliver a PDF + PPTX.

## Agent Chain

```
orchestrator
  └── lead-data
        ├── data-collector    → pulls raw data from public API
        ├── data-cleaner      → validates, deduplicates, fixes types
        ├── statistician      → regression, trend analysis
        ├── gis-specialist    → choropleth map, spatial joins
        ├── visualizer        → charts, tables, infographics
        └── reporter          → assembles final report
```

## Step-by-Step

```bash
# 1. Kick off the chain
python scripts/update_status.py orchestrator working "Monthly housing report — June 2026"
python scripts/update_status.py lead-data working "Pipeline start: collector → reporter"

# 2. Data collection
python scripts/update_status.py data-collector working "Fetching transaction data from open API"
# ... Claude collects ~50,000 rows ...
python scripts/update_status.py data-collector done "52,341 rows fetched, saved to data/raw/housing_2026_06.csv"

# 3. Cleaning
python scripts/update_status.py data-cleaner working "Removing duplicates, fixing null regions"
# ... Claude cleans the data ...
python scripts/update_status.py data-cleaner done "99.1% quality score, 51,887 rows retained"

# 4. Statistics
python scripts/update_status.py statistician working "YoY trend analysis, price index regression"
python scripts/update_status.py statistician done "Avg price +7.3% YoY; 3 outlier districts flagged"

# 5. GIS
python scripts/update_status.py gis-specialist working "Choropleth: price change by district"
python scripts/update_status.py gis-specialist done "18 district polygons mapped, exported to assets/map_june.html"

# 6. Visualization
python scripts/update_status.py visualizer working "Bar charts, trend lines, district table"
python scripts/update_status.py visualizer done "8 charts exported to assets/charts/"

# 7. Report
python scripts/update_status.py reporter working "Assembling PPTX + PDF"
python scripts/update_status.py reporter done "Delivered: reports/housing_report_2026_06.pptx + .pdf"

# 8. Close the chain
python scripts/update_status.py lead-data done "Pipeline complete — all 6 agents done"
python scripts/update_status.py orchestrator done "Housing report June 2026 delivered"
```

## What Gets Persisted

- Every `done` status is logged in `agent_status.json` and shown on the dashboard
- The statistician's methodology is saved to `wiki/notes/method/housing-regression.md`
- The GIS district filter pattern goes to `wiki/notes/method/gis-district-filter.md`
- Next month's run reads these notes automatically — no re-briefing needed

## Issue Tracking

```bash
# Create an issue for a data quality problem discovered mid-pipeline
python scripts/issue_create.py "Null values in Changwon district" \
  "data-cleaner found 143 null region codes" data-cleaner high

# The issue auto-transitions as the agent works:
#   working → in_progress
#   done    → done
```

## Result

A complete, audited pipeline run in the dashboard. All decisions in the wiki. Zero re-explanation next month.
