# Intelligence Analysis Platform (Message Data)

This repository contains the analysis pipeline and reporting system used to process ~900k+ personal messages, build relationship intelligence metrics, and generate the reports under `REPORTS/`.

The goal of this refactor is to make the codebase publish‑ready: a coherent Python project with a clear entrypoint, accurate docs, and a single source of truth for analysis logic.

---

## Overview

At a high level, the system:
- Loads and normalizes exported message data from `DATA/raw/messages.csv`.
- Builds a clean contact database and deep per‑relationship analyses (`analysis_pipeline.py`).
- Runs higher‑level analytics modules (predictive risk, patterns, topics, sentiment, attachment).
- Optionally runs psychological/monitoring modules (communication evolution, conflict analysis, health monitoring, trend reports).
- Generates markdown reports and dashboards in `REPORTS/` and JSON outputs in `outputs/`.

You can keep using the existing final reports as-is, or regenerate them from raw data using the scripts described below.

---

## Repository Structure

Core code and data:

- `analysis_pipeline.py` – canonical loader + core statistics and deep per‑chat analyses.
- `analytics/` – advanced analytics modules:
  - `predictive_analysis.py`
  - `pattern_detection.py`
  - `topic_mining.py`
  - `sentiment_evolution.py`
- `psychology/` – psychological profiling:
  - `attachment_analysis.py` (fully integrated with the core pipeline)
  - `communication_evolution.py` (now uses the same loader; still exploratory)
  - `conflict_analysis.py` (same note as above)
- `reporting/` – higher‑level reporting helpers:
  - `enhanced_report_generator.py`
  - `comparative_analysis.py`
  - `trend_reports.py`
- `monitoring/health_monitor.py` – experimental relationship health monitor.
- `orchestration/run_full_analysis.py` – orchestrates all major analysis modules on selected contacts.
- `DATA/` – raw and derived data:
  - `DATA/raw/messages.csv` – original exported messages (private input data).
  - `DATA/analysis/` – JSON artifacts produced by `analysis_pipeline.py`.
- `REPORTS/` – generated human‑readable reports and visualizations (see `REPORTS/README.md`).

Historical planning/status docs that remain relevant:

- `ENHANCEMENT_PLAN_V3.md` – v3 architecture and enhancement plan.
- `IMPLEMENTATION_STATUS.md` – module‑by‑module status snapshot (kept as a historical reference).
- `IQ_AND_JESSICA_ANALYSIS.md` – full write‑up of IQ/EI and Jessica deep‑dive.

See `CHANGELOG.md` for a high‑level history of major milestones.

---

## Requirements

The core pipeline and analytics modules expect:

- Python 3.10+ (tested with 3.11/3.12)
- Python packages:
  - `pandas`
  - `numpy`
  - `scipy`
  - `scikit-learn`

Install dependencies (example):

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install pandas numpy scipy scikit-learn
```

Some experimental modules may require additional libraries (e.g., plotting, NLP), but the core analytics and pipeline only rely on the packages above.

---

## Data Expectations

`analysis_pipeline.load_messages()` expects a CSV at `DATA/raw/messages.csv` with at least:

- `Chat Session` – conversation identifier
- `Message Date` – timestamp
- `Sender Name` – original sender label from export
- `Text` – message body
- `Type` – direction (e.g. `"outgoing"` vs other)

The loader normalizes this into:

- `chat_session`, `timestamp`, `sender_name`, `message`, `type`, plus a derived `sender` column (`"You"` for outgoing, otherwise sender name).

Higher‑level modules now consistently build on top of this unified schema.

---

## Running the Core Pipeline

1. **Prepare data**
   - Place your exported messages CSV at `DATA/raw/messages.csv` with the expected columns.

2. **Rebuild core analyses**

   ```bash
   python analysis_pipeline.py
   ```

   This will:
   - Normalize and load `DATA/raw/messages.csv`.
   - Build a clean contact database and summary statistics.
   - Generate deep per‑relationship JSON files under `DATA/analysis/*_deep_analysis.json`.

3. **Run individual analytics modules (optional)**

   Each module can be run standalone; they will read from the same raw data via `analysis_pipeline.load_messages()`:

   ```bash
   # Predictive analysis
   python analytics/predictive_analysis.py

   # Pattern detection
   python analytics/pattern_detection.py

   # Topic mining
   python analytics/topic_mining.py

   # Sentiment evolution
   python analytics/sentiment_evolution.py

   # Attachment analysis
   python psychology/attachment_analysis.py
   ```

   These commands write JSON outputs under `outputs/` (e.g. `outputs/predictions`, `outputs/patterns`, `outputs/topics`, `outputs/sentiment`, `outputs/attachment`).

4. **Run the orchestrated full analysis**

   ```bash
   # Run all modules on the default priority contact list (top contacts by volume)
   python orchestration/run_full_analysis.py --all

   # Run a single module for a specific contact
   python orchestration/run_full_analysis.py --contact "Some Contact Name" --module predictive
   ```

   The orchestrator:
   - Loads data and deep analyses once via `analysis_pipeline`.
   - Runs predictive, pattern, topic, sentiment, attachment, communication‑evolution, and conflict modules where data is sufficient.
   - Saves per‑module JSON outputs using the module‑specific save helpers.
   - Writes an aggregated `outputs/MASTER_ANALYSIS_SUMMARY.json`.

5. **(Optional) Generate enhanced markdown reports**

   Once JSON outputs exist under `outputs/`, you can experiment with:

   ```bash
   python reporting/enhanced_report_generator.py
   ```

   This module is still evolving; consult its docstring and source for details.

---

## Using the Existing Final Reports

If you simply want to explore the original full analysis that was already generated (without re‑running the pipeline):

- Start with the interactive dashboard: `REPORTS/01_EXECUTIVE_SUMMARY/DASHBOARD.html`.
- Or read the executive summary: `REPORTS/01_EXECUTIVE_SUMMARY/EXECUTIVE_SUMMARY.md`.
- For navigation across all reports, see `REPORTS/README.md` and `REPORTS/MASTER_INDEX.md`.

All of the IQ/EI findings and relationship deep dives referenced in the old README are preserved in these reports.

---

## Status & Roadmap

- Core v2/v3 analysis pipeline and the main analytics modules are functional and wired through the unified loader.
- Psychological and monitoring modules (`communication_evolution`, `conflict_analysis`, `health_monitor`, `trend_reports`) now read from the same normalized data but should still be considered **experimental**.
- Future work (per `ENHANCEMENT_PLAN_V3.md` and `IMPLEMENTATION_STATUS.md`) includes:
  - ML model training and persistence.
  - Rich interactive dashboards and advanced visualizations.
  - Real‑time monitoring and alerting.

See `CHANGELOG.md` for a concise history of major steps, and `ENHANCEMENT_PLAN_V3.md` for the longer‑form architecture plan.

---

## Publishing Notes

Before publishing this repository publicly:

- **Data privacy:** `DATA/raw/messages.csv` and many `REPORTS/` files contain highly personal content. Consider removing or replacing them with synthetic/sample data.
- **License:** No explicit open‑source license has been set yet. Decide on and add a `LICENSE` file before public release.
- **Dependencies:** If you want a stricter environment specification, add a `requirements.txt` or `pyproject.toml` that matches the versions you actually use.

With those caveats, the codebase and documentation are now structured to be understandable and usable by someone who did not participate in the original project.
