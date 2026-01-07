# Architecture Overview

This document describes the high‑level architecture of the message‑based Intelligence Analysis Platform and how the Python modules fit together after refactoring.

The goal is to make the system understandable and evolvable: a clear data flow, well‑defined layers, and consistent entrypoints instead of one‑off scripts.

---

## 1. Layers and Responsibilities

### 1.1 Data & Core Analysis Layer

**Purpose:** Load raw message data once, normalize it, and compute reusable core artifacts that higher‑level modules can rely on.

- `DATA/raw/messages.csv`
  - Single source of truth for the exported messages.
  - Required columns: `Chat Session`, `Message Date`, `Sender Name`, `Text`, `Type`.

- `analysis_pipeline.py`
  - `load_messages(path="DATA/raw/messages.csv") -> DataFrame`
    - Normalizes raw CSV into a canonical schema:
      - `chat_session`, `timestamp`, `sender_name`, `message`, `type`, `sender`.
  - `build_contact_database(df)`
    - Constructs a per‑chat contact database and `ChatStats` objects with classification into `individual`, `group`, `system`.
  - `compute_basic_stats(df, chat_stats)`
    - Global statistics (message counts, date ranges, year breakdown, top contacts).
  - `build_all_individuals_and_groups(chat_stats)`
    - Sorted lists of individuals and groups by message volume.
  - `_build_emotional_lexicon`, `_count_emotional_keywords`
    - Shared lexicon and counting logic for deep emotional keyword analysis.
  - `_build_phases`, `build_deep_analysis_for_chat`, `rebuild_all_deep_analyses`
    - Deep per‑relationship analyses: phases, intensity, balance, emotional keyword counts, status.

**Outputs:**
- JSON artifacts under `DATA/analysis/` (contact database, basic stats, deep analyses per contact).
- These are the shared “core features” all higher‑level modules can draw from.

### 1.2 Analytics Layer (Data‑Driven Relationship Metrics)

**Purpose:** Provide focused analytical views on top of the normalized data and deep analyses.

All analytics modules operate on the **same normalized DataFrame** produced by `load_messages`, and some also use deep analyses from `analysis_pipeline`.

- `analytics/predictive_analysis.py` – `RelationshipPredictor`
  - Constructor: `RelationshipPredictor(df, deep_analyses)`
  - Responsibilities:
    - Extract predictive features from deep analyses (phases, emotional keywords, balance, recency).
    - Heuristically score breakup risk and generate warning signs (`calculate_breakup_risk`).
    - Project communication trajectories (`predict_trajectory`).
    - Compare current relationship to ended ones (`compare_to_historical`).
    - Produce a consolidated prediction report (`generate_full_prediction_report`).
  - Persistence:
    - `save_prediction_report(report, output_dir="outputs/predictions")`.

- `analytics/pattern_detection.py` – `PatternDetector`
  - Constructor: `PatternDetector(df)`
  - Responsibilities:
    - Anomaly detection (gaps, spikes).
    - Turning point detection (communication phase changes).
    - Recurring cycles (weekly patterns, autocorrelation).
    - Response time and initiation pattern analysis.
    - Consolidated pattern report (`generate_full_pattern_report`).
  - Persistence:
    - `save_pattern_report(report, "outputs/patterns")`.

- `analytics/topic_mining.py` – `TopicMiner`
  - Constructor: `TopicMiner(df)`
  - Responsibilities:
    - LDA‑based topic extraction and evolution over time.
    - Conflict‑specific topic identification.
    - Consolidated topic report (`generate_full_topic_report`).
  - Persistence:
    - `save_topic_report(report, "outputs/topics")`.

- `analytics/sentiment_evolution.py` – `SentimentAnalyzer`
  - Constructor: `SentimentAnalyzer(df)`
  - Responsibilities:
    - Build a custom sentiment lexicon and score each message.
    - Track sentiment progression over phases.
    - Calculate emotional volatility and detect shifts.
    - Compare sentiment between participants.
    - Consolidated sentiment report (`generate_full_sentiment_report`).
  - Persistence:
    - `save_sentiment_report(report, "outputs/sentiment")`.

### 1.3 Psychology Layer

**Purpose:** Interpret communication patterns in terms of psychological constructs (attachment styles, communication evolution, conflict).

- `psychology/attachment_analysis.py` – `AttachmentAnalyzer`
  - Constructor: `AttachmentAnalyzer(df)` where `df` is the normalized messages DataFrame.
  - Responsibilities:
    - Infer overall attachment profile across significant relationships.
    - Compute contact‑specific attachment indicators and styles.
    - Assess compatibility and dynamics between your style and theirs.
    - Consolidated attachment report (`generate_full_attachment_report`).
  - Persistence:
    - `save_attachment_report(report, "outputs/attachment")`.

- `psychology/communication_evolution.py` – `CommunicationEvolutionAnalyzer`
  - Now uses `analysis_pipeline.load_messages` and a harmonized schema (`contact_name`, `message_content`, `is_from_me`).
  - Responsibilities:
    - Formally:
      - Communication formality evolution.
      - Emotional vocabulary and expressiveness.
      - Question patterns and engagement.
      - Listening indicators.
      - Linguistic synchronization.
      - Vulnerability and self‑disclosure patterns.
    - Primary API:
      - `analyze_contact(contact_name) -> dict`
      - `save_results(results, "outputs/communication_evolution")`.

- `psychology/conflict_analysis.py` – `ConflictAnalyzer`
  - Now uses `analysis_pipeline.load_messages` and the same harmonized schema.
  - Responsibilities:
    - Identify conflict periods from rolling conflict scores.
    - Characterize conflict statistics (frequency, duration, severity).
    - Detect conflict triggers and resolution strategies.
    - Track conflict “maturity” over time.
    - Primary API:
      - `analyze_contact(contact_name) -> dict`
      - `save_results(results, "outputs/conflict_analysis")`.

### 1.4 Monitoring & Reporting Layer

**Purpose:** Track health over time across relationships and synthesize human‑readable outputs from the analytics and psychology layers.

- `monitoring/health_monitor.py` – `HealthMonitor`
  - Now built on `load_messages` with standardized `contact_name` + `is_from_me`.
  - Responsibilities:
    - Compute relationship health scores from:
      - Communication frequency.
      - Balance.
      - Recency.
      - Trend.
      - Consistency.
    - Track health trajectories and detect changes.

- `reporting/trend_reports.py` – `TrendAnalyzer`
  - Also built on `load_messages` and the harmonized schema.
  - Responsibilities:
    - Personal growth over time (yearly breakdowns).
    - Cross‑relationship pattern analysis (balance, duration, rate).
    - Network health / trajectory.

- `reporting/enhanced_report_generator.py` – `EnhancedReportGenerator`
  - Responsibilities:
    - Load module outputs from `outputs/*`.
    - Compose a comprehensive markdown report for a contact by stitching together:
      - Predictive, pattern, topic, sentiment, attachment, communication, and conflict sections.
    - Provide a single, enriched human‑readable report per contact.

### 1.5 Orchestration Layer

**Purpose:** Provide a single entrypoint that:
- Loads core data once.
- Initializes analyzers.
- Runs them in a consistent way across a set of contacts.
- Persists outputs and optional summary exports.

- `orchestration/run_full_analysis.py` – `FullAnalysisOrchestrator`
  - Initialization:
    - Uses `analysis_pipeline.load_messages` to load the raw messages.
    - Builds `contact_db` and `chat_stats` via `build_contact_database`.
    - Rebuilds deep analyses via `rebuild_all_deep_analyses`.
    - Initializes analyzers:
      - `RelationshipPredictor(self.df, self.deep_analyses)`
      - `PatternDetector(self.df)`
      - `TopicMiner(self.df)`
      - `SentimentAnalyzer(self.df)`
      - `AttachmentAnalyzer(self.df)`
      - `CommunicationEvolutionAnalyzer(data_path)`
      - `ConflictAnalyzer(data_path)`
  - Internal wrapper methods:
    - `_run_predictive(contact)`
    - `_run_patterns(contact)`
    - `_run_topics(contact)`
    - `_run_sentiment(contact)`
    - `_run_attachment(contact)`
  - Public API:
    - `run_all_analyses(contacts=None, skip_errors=True) -> dict`
      - Iterates contacts (default priority list).
      - Runs each module, collecting results and saving JSON via module‑specific `save_*` helpers.
      - Produces `outputs/MASTER_ANALYSIS_SUMMARY.json`.
    - `run_single_module(module_name, contact) -> dict`
      - Runs a single module for one contact using the same wrappers.
    - `export_to_csv("outputs/analysis_export.csv")`
      - Aggregates key metrics from per‑contact results into a CSV for quick review.

  - CLI:
    - `python orchestration/run_full_analysis.py --all`
    - `python orchestration/run_full_analysis.py --contact "Jessica"`
    - `python orchestration/run_full_analysis.py --contact "Jessica" --module predictive`

---

## 2. Data Flow

1. **Ingestion**
   - Raw CSV at `DATA/raw/messages.csv` is loaded and normalized by `analysis_pipeline.load_messages`.

2. **Core Analyses**
   - `build_contact_database`, `compute_basic_stats`, `rebuild_all_deep_analyses` are run once to produce:
     - `contact_db`, `chat_stats`, `deep_analyses`, and JSON files in `DATA/analysis/`.

3. **Analytics & Psychology**
   - The orchestrator passes the shared DataFrame and deep analyses into analytics/psychology modules:
     - `RelationshipPredictor`, `PatternDetector`, `TopicMiner`, `SentimentAnalyzer`, `AttachmentAnalyzer`.
   - Psychology modules that rely on per‑message content (`communication_evolution`, `conflict_analysis`, `health_monitor`, `trend_reports`) also use `load_messages`, but now on the same canonical schema (via renaming and `is_from_me`).

4. **Outputs**
   - Each module writes JSON reports to its own directory under `outputs/`.
   - `EnhancedReportGenerator` can then read those JSONs and synthesize enriched markdown reports.
   - The orchestrator aggregates everything into `outputs/MASTER_ANALYSIS_SUMMARY.json` and an optional CSV export.

---

## 3. Design Principles Going Forward

1. **Single Source of Truth for Data Loading**
   - All modules should read message data via `analysis_pipeline.load_messages`.
   - No module should directly `read_csv` from `DATA/raw/messages.csv`.

2. **Explicit, Typed Interfaces**
   - Contact‑level analyzers expose a single primary method:
     - Either `generate_full_*_report(contact_name)` or `analyze_contact(contact_name)`.
   - Saving is handled by dedicated `save_*` helpers so orchestrators don’t duplicate file naming logic.

3. **Separation of Concerns**
   - Core analysis (counts, phases, lexicons) lives in `analysis_pipeline`.
   - Analytics modules build on these to generate advanced metrics and predictions.
   - Psychology modules interpret behavioral patterns.
   - Monitoring/reporting modules aggregate and present results.
   - Orchestration modules wire everything together; they do not implement analysis logic.

4. **Extensibility**
   - To add a new analyzer:
     - Implement it in a new module (e.g., `analytics/new_dimension.py`).
     - Accept `df` and/or `deep_analyses` in the constructor.
     - Provide a `generate_full_*_report(contact_name)` and `save_*_report()`.
     - Register it in the orchestrator’s module list with a small wrapper (if needed).

5. **Backward Compatibility vs. Public API**
   - Legacy scripts and reports remain in place (especially under `REPORTS/` and `DATA/analysis/`) for historical reference.
   - The “public” surface for programmatic use is now:
     - `analysis_pipeline.load_messages` and helper functions.
     - The analytics and psychology classes described above.
     - `FullAnalysisOrchestrator` as the primary orchestration entrypoint.

This architecture keeps existing capabilities intact but makes the system easier to understand: one way to load data, clear module boundaries, consistent reporting patterns, and a single orchestration layer that ties it all together. 

