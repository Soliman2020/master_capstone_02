# Project 02 — Statistical Analysis

## Goal

Conduct hypothesis tests on synthetic surveillance events and access-control
logs produced in [Project 01](../project_01_reproducible_workflows/). The
analysis evaluates whether zone restrictiveness, event type, and time of day
show statistically meaningful patterns that can inform the rule-engine design
for the final AI Security Operations Copilot.

## Dataset

The notebook reads the **processed** outputs from Project 01:

| File | Rows | Columns |
|---|---|---|
| `data/processed/surveillance_events.parquet` | 988 | `event_id`, `event_timestamp`, `site_id`, `zone_id`, `device_id`, `event_type`, `confidence_score` |
| `data/processed/access_logs.parquet` | 9,847 | `log_id`, `log_timestamp`, `site_id`, `zone_id`, `device_id`, `badge_id`, `user_id`, `outcome` |

Processed data is used instead of raw data because the raw files intentionally
contain 5% injected dirty rows (missing timestamps, out-of-range confidence
scores, unknown outcomes) that were cleaned in Project 01.

## What the notebook does

`notebooks/02_statistical_analysis.ipynb` runs a complete statistical workflow:

1. **Data ingestion** — loads Parquet files and prints row counts.
2. **Descriptive statistics** — `describe(include="all")`, event-type counts,
   site counts, access-outcome counts, zone counts.
3. **Visualizations** — three saved plots in `reports/`:
   - `viz1_access_by_zone.png` — access-outcome rate by zone type
   - `viz2_confidence_by_event.png` — confidence-score distribution by event type
   - `viz3_access_by_hour.png` — access-log volume by hour of day
4. **Hypothesis tests**:
   - Chi-square test of independence: zone type vs. access outcome
   - Independent-samples t-test: intrusion vs. normal-motion confidence
5. **Effect-size reporting** — Cramér's V for the chi-square test.
6. **Interpretation** — test selection justification, results, cross-visual
   comparison, limitations/bias.
7. **Summary** — key findings, challenges, next steps, reproducibility notes.
8. **References** — Agresti (2002), Student (1908), Ruxton (2006), Cohen (1988).

## Key findings

- **Zone type vs. access outcome**: χ²(1, N=9,173) = 4.491, *p* = 0.0341,
  Cramér's V = 0.0221. Statistically significant but practically negligible.
  The graph in `reports/viz1_access_by_zone.png` shows a marginally lower
  denial rate in restricted zones than in unrestricted zones, confirming that
  the signal is too weak to drive the rule engine on its own.
- **Intrusion vs. normal motion confidence**: t(778) = 7.852,
  *p* = 1.36 × 10⁻¹⁴, Δ ≈ 0.21. Strong separation supports using confidence as
  a discriminative feature. The mean intrusion confidence (0.825) is slightly
  below the `confidence > 0.85` threshold, so that cutoff needs separate
  precision/recall validation.
- **Hour-of-day distribution**: approximately uniform in the synthetic data;
  after-hours (17:00–23:00) is 28.9% of logs. The after-hours rule is not
  validated by this dataset because the generator samples timestamps uniformly.

## Environment

The project includes its own virtual environment and `requirements.txt`.

```bash
# Create and activate the environment (example with venv on Windows)
python -m venv p2_venv
.\p2_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

To regenerate `requirements.txt` from the active environment:

```bash
pip freeze > requirements.txt
```

## How to run

```bash
# Activate the environment
.\p2_venv\Scripts\activate

# Launch JupyterLab
jupyter lab notebooks/02_statistical_analysis.ipynb
```

Then run all cells with **Kernel → Restart Kernel and Run All Cells**. The
notebook executes top-to-bottom without errors in a fresh environment.

## Reproducibility

- `SEED = 42` is set in the first code cell for all NumPy random operations.
- The synthetic datasets in `data/processed/` are deterministic outputs of the
  Project 01 generator, so re-running Project 01 followed by this notebook
  produces identical results.

## Project structure

```
project_02_statistical_analysis/
├── README.md                              # this file
├── requirements.txt                       # frozen Python dependencies
├── notebooks/
│   └── 02_statistical_analysis.ipynb    # full analysis notebook
├── data/
│   └── processed/                         # cleaned data from Project 01
│       ├── surveillance_events.parquet
│       ├── surveillance_events.csv
│       ├── access_logs.parquet
│       └── access_logs.csv
├── reports/                               # exported visualizations and reports
│   ├── Statistical_Analysis_Report.md   # full written report (markdown)
│   ├── Statistical_Analysis_Report.pdf  # full written report (PDF)
│   ├── module_summary.md                  # concise module summary (markdown)
│   ├── module_summary.pdf                 # concise module summary (PDF)
│   ├── viz1_access_by_zone.png
│   ├── viz2_confidence_by_event.png
│   └── viz3_access_by_hour.png
└── src/
    ├── __init__.py                        # module marker
    ├── constants.py                       # SEED and output-path constants
    └── generators.py                      # deterministic synthetic data generator
```

### Source files

| File | Purpose | Run command |
|---|---|---|
| `src/constants.py` | Defines `SEED = 42`, output paths, and directory helpers used by the generator. | Imported by `generators.py` |
| `src/generators.py` | Deterministically generates `surveillance_events` and `access_logs` Parquet/CSV files in `data/processed/`. | `python src/generators.py` |

## Reports

- The report content is also available in `Statistical_Analysis_Report.md` and
  `module_summary.md` for easy editing and PDF conversion.

| File | Format | Audience |
|---|---|---|
| `reports/Statistical_Analysis_Report.md` | Markdown | Technical reviewers; source for PDF conversion |
| `reports/Statistical_Analysis_Report.pdf` | PDF | Formal submission / portfolio |
| `reports/module_summary.md` | Markdown | Technical + non-technical readers; source for PDF conversion |
| `reports/module_summary.pdf` | PDF | Concise submission / portfolio |

Convert from Markdown to PDF with the tool of your choice (e.g., `md2pdf.py`, Pandoc, or a word processor).

---

## Limitations

- All data is synthetic. Significant p-values reflect the generator's explicit
  rules rather than real-world access-control behavior.
- The after-hours distribution is uniform by design, so the project's
  after-hours rule is not validated here.


## License

This project is part of the Udacity AI Mastery Capstone and is intended for
educational and portfolio use only.
