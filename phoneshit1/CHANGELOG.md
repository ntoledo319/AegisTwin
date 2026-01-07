# Changelog

All notable changes to this project are documented here.

## Unreleased

- Cleaned up the orchestration layer to use the shared `analysis_pipeline` data loader and deep-analysis index.
- Normalized psychological and monitoring modules (`communication_evolution`, `conflict_analysis`, `health_monitor`, `trend_reports`) to load data via `analysis_pipeline.load_messages`.
- Consolidated and removed several ad-hoc progress tracker documents in favor of this changelog and an updated `README.md`.

## 2025-11-24 – v3 Analytics & Attachment Modules

- Added advanced analytics modules: predictive analysis, pattern detection, topic mining, and sentiment evolution under `analytics/`.
- Implemented attachment analysis under `psychology/attachment_analysis.py`, integrated with the v2 core analysis.
- Drafted the v3 enhancement plan and implementation status documents describing planned ML, visualization, and monitoring components.

## 2025-11-23 – v2 Reports, Reorganization, and QA

- Reorganized report outputs into the current `REPORTS/` hierarchy with a master index and navigation READMEs.
- Generated hundreds of markdown reports and visualizations covering top relationships, personal profile, and executive summaries.
- Fixed categorization issues, emotional-intelligence score miscalculation, and multiple report labeling / data consistency bugs.
- Performed large-scale cleanup of legacy directories and shallow report variants, keeping a single, well-structured report set.

## 2025-11-21 – IQ & Jessica Deep Dive

- Completed IQ assessment and message-based emotional-intelligence analysis.
- Produced a detailed IQ/EI profile and an in-depth relationship analysis for Jessica based on message history.

