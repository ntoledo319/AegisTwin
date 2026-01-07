# AegisTwin Codebase Inventory

**Generated:** 2026-01-06  
**Tag:** `baseline-import`  
**Branch:** `aegistwin-productize`

---

## Code Roots

### 1. HydraMind_v1/ (KEEP - Runtime Spine)
- **Package:** `hydramind/`
- **Purpose:** Event-driven agent runtime with policy engine, event bus, replay service
- **Status:** ✅ KEEP - wrap with AegisTwin layer

### 2. DigitalTwin/ (PARTIAL KEEP)
- **Package:** `integrated_system/` ✅ KEEP (connectors + KG)
- **Package:** `advanced-data-analysis-twin/digital_twin/memory/` ✅ KEEP (memory system)
- **Retire Candidates:**
  - `cognilink/` - redundant
  - `ct_omega/` - redundant  
  - `ct_modules/` - redundant
  - `mindmirror/` - redundant
  - `outputs/`, `logs/`, `data/` - data artifacts
  - `summarized_conversations/` - PII HAZARD (2942 items)

### 3. phoneshit1/ (DATA HAZARD - NON-SHIPPABLE)
- **Status:** ❌ RETIRE ENTIRELY
- **Salvage only:** UI styling patterns (rebuild with synthetic data)
- **Contains:** Real conversation exports, personal names, contact databases

---

## Entrypoints

| Source | Entrypoint | Type |
|--------|-----------|------|
| HydraMind_v1 | `hydramind/__main__.py` | CLI |
| HydraMind_v1 | `hydramind/control/api.py` | FastAPI |
| DigitalTwin | `integrated_system/main.py` | App |
| DigitalTwin | `advanced-data-analysis-twin/main.py` | App |
| phoneshit1 | `analysis_pipeline.py` | Script |

---

## Dependency Files

| Path | Type |
|------|------|
| `HydraMind_v1/requirements.txt` | pip |
| `HydraMind_v1/setup.py` | setuptools |
| `DigitalTwin/requirements.txt` | pip |
| `DigitalTwin/pyproject.toml` | PEP 517 |
| `DigitalTwin/advanced-data-analysis-twin/requirements.txt` | pip |

---

## Suspected PII Locations (MUST QUARANTINE)

### CRITICAL - phoneshit1/
```
phoneshit1/11:20Messages - 1180 chat sessions.csv          # 112MB real messages
phoneshit1/jessica_conversation.txt                         # Personal conversation
phoneshit1/jessica_raw_data.csv                            # Personal data export
phoneshit1/jessica_raw_data.json                           # Personal data export
phoneshit1/jessica_metadata.json                           # Personal metadata
phoneshit1/DATA/raw/messages.csv                           # Raw message export
phoneshit1/DATA/analysis/contact_database.json             # Contact DB
phoneshit1/DATA/analysis/contact_database_v2.json          # Contact DB
phoneshit1/DATA/analysis/jessica_*.json                    # Personal analysis
phoneshit1/DATA/analysis/*_deep_analysis.json              # Name-based analysis
phoneshit1/outputs/                                        # All analysis outputs with names
phoneshit1/REPORTS/                                        # Reports with personal data
phoneshit1/summarized_conversations/                       # Real conversations
phoneshit1/top_relationships.json                          # Personal relationships
phoneshit1/IQ_AND_JESSICA_ANALYSIS.md                     # Personal analysis doc
```

### HIGH - DigitalTwin/
```
DigitalTwin/messages_complete.json.zip                     # 90MB message archive
DigitalTwin/summarized_conversations/                      # 2942 conversation files
DigitalTwin/data/                                          # Data directory
DigitalTwin/logs/                                          # Log files
DigitalTwin/outputs/                                       # Output artifacts
DigitalTwin/cognilink/data/sample/sample_messages.json    # Sample messages (verify)
```

### MEDIUM - HydraMind_v1/
```
HydraMind_v1/brain_events.sqlite                          # Event store (verify synthetic)
HydraMind_v1/logs/hydramind.log                           # Runtime logs
HydraMind_v1/snapshots/telemetry.mmap                     # Telemetry data
```

---

## Key Components to Preserve

### From integrated_system/
- `data_processing/connectors/` - Email, calendar, messages, social connectors
- `knowledge_graph/` - Graph builder, query, visualization
- `digital_twin/memory/` - Memory system
- `analysis/` - Cognitive, communication, advanced analysis

### From advanced-data-analysis-twin/digital_twin/
- `memory/` - Episodic, semantic, procedural memory systems
- `adapters/` - Various analysis adapters
- `evolution/` - Adaptive engine, safety validator

### From hydramind/
- `core/` - Bus, config, policy, event store, module system
- `modules/` - Intelligence modules (replay, pattern, anomaly)
- `control/` - API layer

---

## Next Steps
1. Run `tools/pii_scan.py` to generate detailed PII report
2. Move all suspected PII to `/graveyard/PII/`
3. Generate synthetic fixtures
4. Build AegisTwin wrapper package
