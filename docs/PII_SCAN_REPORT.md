# PII Scan Report

**Scan Time:** 2026-01-06T19:22:23.147729
**Files Scanned:** 519
**Total Findings:** 279

## Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 3 |
| 🟠 HIGH | 196 |
| 🟡 MEDIUM | 80 |
| 🟢 LOW | 0 |

## Quarantined Paths (Excluded from scan)

- `graveyard/PII`
- `graveyard/PII/hm_logs`
- `graveyard/PII/dt_summarized_conversations`
- `graveyard/PII/phoneshit1`
- `graveyard/PII/phoneshit1/reporting`
- `graveyard/PII/phoneshit1/summarized_conversations`
- `graveyard/PII/phoneshit1/psychology`
- `graveyard/PII/phoneshit1/.enodios`
- `graveyard/PII/phoneshit1/.enodios/runs`
- `graveyard/PII/phoneshit1/.enodios/runs/op_1765863321797`
- `graveyard/PII/phoneshit1/orchestration`
- `graveyard/PII/phoneshit1/monitoring`
- `graveyard/PII/phoneshit1/DATA`
- `graveyard/PII/phoneshit1/DATA/analysis`
- `graveyard/PII/phoneshit1/DATA/raw`
- `graveyard/PII/phoneshit1/outputs`
- `graveyard/PII/phoneshit1/outputs/patterns`
- `graveyard/PII/phoneshit1/outputs/attachment`
- `graveyard/PII/phoneshit1/outputs/conflict_analysis`
- `graveyard/PII/phoneshit1/outputs/sentiment`
- `graveyard/PII/phoneshit1/outputs/communication_evolution`
- `graveyard/PII/phoneshit1/outputs/predictions`
- `graveyard/PII/phoneshit1/outputs/topics`
- `graveyard/PII/phoneshit1/analytics`
- `graveyard/PII/phoneshit1/REPORTS`
- `graveyard/PII/phoneshit1/REPORTS/05_ENHANCED`
- `graveyard/PII/hm_snapshots`
- `graveyard/PII/dt_logs`
- `graveyard/PII/dt_outputs`
- `graveyard/PII/dt_data`
- `graveyard/PII/dt_data/__MACOSX`
- `graveyard/PII/cognilink_sample`
- `graveyard/RETIRED_CODE`
- `graveyard/RETIRED_CODE/ct_omega`
- `graveyard/RETIRED_CODE/ct_omega/demo_data`
- `graveyard/RETIRED_CODE/ct_omega/demo_data/profiles`
- `graveyard/RETIRED_CODE/ct_omega/core`
- `graveyard/RETIRED_CODE/ct_omega/test_data`
- `graveyard/RETIRED_CODE/ct_omega/test_data/profiles`
- `graveyard/RETIRED_CODE/ct_omega/docs`
- `graveyard/RETIRED_CODE/cognilink`
- `graveyard/RETIRED_CODE/cognilink/pipeline`
- `graveyard/RETIRED_CODE/cognilink/pipeline/connectors`
- `graveyard/RETIRED_CODE/cognilink/pipeline/processors`
- `graveyard/RETIRED_CODE/cognilink/interface`
- `graveyard/RETIRED_CODE/cognilink/interface/web`
- `graveyard/RETIRED_CODE/cognilink/interface/templates`
- `graveyard/RETIRED_CODE/cognilink/core`
- `graveyard/RETIRED_CODE/cognilink/analysis`
- `graveyard/RETIRED_CODE/cognilink/config`
- `graveyard/RETIRED_CODE/cognilink/tests`
- `graveyard/RETIRED_CODE/cognilink/tests/unit`
- `graveyard/RETIRED_CODE/cognilink/tests/integration`
- `graveyard/RETIRED_CODE/cognilink/examples`
- `graveyard/RETIRED_CODE/cognilink/templates`
- `graveyard/RETIRED_CODE/cognilink/data`
- `graveyard/RETIRED_CODE/mindmirror`
- `graveyard/RETIRED_CODE/mindmirror/interface`
- `graveyard/RETIRED_CODE/mindmirror/interface/cli`
- `graveyard/RETIRED_CODE/mindmirror/interface/api`
- `graveyard/RETIRED_CODE/mindmirror/core`
- `graveyard/RETIRED_CODE/mindmirror/analysis`
- `graveyard/RETIRED_CODE/mindmirror/models`
- `graveyard/RETIRED_CODE/mindmirror/models/cognitive`
- `graveyard/RETIRED_CODE/mindmirror/models/memory`
- `graveyard/RETIRED_CODE/mindmirror/models/language`
- `graveyard/RETIRED_CODE/mindmirror/models/decision`
- `graveyard/RETIRED_CODE/ct_modules`
- `graveyard/RETIRED_CODE/ct_modules/shared`
- `graveyard/RETIRED_CODE/ct_modules/shared/core`
- `graveyard/RETIRED_CODE/ct_modules/shared/models`
- `graveyard/RETIRED_CODE/ct_modules/SONAR`
- `graveyard/RETIRED_CODE/ct_modules/SONAR/tests`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/memory`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/personality`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/tests`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/tests/integration`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/tests/adapters`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/adapters`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/examples`
- `graveyard/RETIRED_CODE/ct_modules/digital_twin/conversation`
- `graveyard/RETIRED_CODE/ct_modules/GRANULAR_BOOST`
- `graveyard/RETIRED_CODE/ct_modules/GRANULAR_BOOST/app`
- `graveyard/RETIRED_CODE/ct_modules/GRANULAR_BOOST/tests`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS/app`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS/app/core`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS/app/models`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS/app/db`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS/app/db/models`
- `graveyard/RETIRED_CODE/ct_modules/LUMOS/app/api`
- `graveyard/RETIRED_CODE/ct_modules/ATLAS`
- `graveyard/RETIRED_CODE/ct_modules/ATLAS/tests`
- `graveyard/RETIRED_CODE/ct_modules/VERVE`
- `graveyard/RETIRED_CODE/ct_modules/VERVE/app`
- `graveyard/RETIRED_CODE/ct_modules/VERVE/app/routers`
- `graveyard/RETIRED_CODE/ct_modules/VERVE/tests`
- `graveyard/RETIRED_CODE/ct_modules/INFINITY`
- `graveyard/RETIRED_CODE/ct_modules/INFINITY/app`
- `graveyard/RETIRED_CODE/ct_modules/INFINITY/app/routers`
- `graveyard/RETIRED_CODE/ct_modules/INFINITY/tests`

## Findings

### CRITICAL (3)

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/DEPLOYMENT.md**
  - Type: `ssn_pattern`
  - Found ssn_pattern pattern
  - Line: 295

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/CONFIGURATION.md**
  - Type: `ssn_pattern`
  - Found ssn_pattern pattern
  - Line: 352

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/setup.py**
  - Type: `ssn_pattern`
  - Found ssn_pattern pattern
  - Line: 166

### HIGH (196)

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/synth_data_gen.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 95

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/synth_data_gen.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 96

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/synth_data_gen.py**
  - Type: `personal_name`
  - Contains personal names: quinn

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/pii_scan.py**
  - Type: `personal_name`
  - Contains personal names: jessica, becca, gabby, lily, marisa, max, mom, potato, steph, ian, julia, oliver, phillip, sean, natalia, quinn

- **HydraMind_v1/banani-ui-export.zip**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: export

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/tests/test_infrastructure_sensors.py**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 118

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/tests/test_infrastructure_sensors.py**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 118

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/tests/test_execs.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/brain.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/core/logging.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/core/policy.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/core/module.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/core/execs.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/data_collector.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/predictive_engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/self_optimizer.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/replay_service.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/pattern_learner.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/seed_optimizer.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/meta_planner.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/swarm_coordinator.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/hydramind/modules/intelligence/optimizer_suite.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/CONFIGURATION.md**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/examples/seed_cognitive_demo.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/docs/PII_SCAN_REPORT.md**
  - Type: `personal_name`
  - Contains personal names: jessica, becca, gabby, lily, marisa, max, mom, potato, steph, ian, julia, oliver, phillip, sean, natalia, quinn

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/docs/01_PRIVACY_AND_PURGE.md**
  - Type: `personal_name`
  - Contains personal names: jessica

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/diligence_pack/PII_PURGE_REPORT.md**
  - Type: `personal_name`
  - Contains personal names: jessica, max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 15

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 23

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 31

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 39

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 47

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 12

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 13

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 20

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 21

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 28

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `personal_name`
  - Contains personal names: quinn

- **fixtures/messages.json**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: messages?(?:_complete)?

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/messages.json**
  - Type: `personal_name`
  - Contains personal names: quinn

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 15

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 23

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 31

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 39

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 47

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 12

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 13

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 20

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 21

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 28

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `personal_name`
  - Contains personal names: quinn

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/emails.json**
  - Type: `personal_name`
  - Contains personal names: quinn

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/calendar_events.json**
  - Type: `personal_name`
  - Contains personal names: quinn

- **fixtures/contacts.json**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: contact

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 8

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 16

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 24

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 32

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `phone_number`
  - Found phone_number pattern
  - Line: 40

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 5

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 6

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 13

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 14

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 21

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `personal_name`
  - Contains personal names: quinn

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/aegistwin/demos/runner.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 48

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/aegistwin/demos/runner.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 48

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/aegistwin/demos/runner.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 49

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/aegistwin/demos/runner.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 49

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_data_connector_example.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/UPDATED_COMPLETION_PLAN.md**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/core/utils.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/analysis/patterns/detectors.py**
  - Type: `personal_name`
  - Contains personal names: max, mom

- **DigitalTwin/advanced-data-analysis-twin/tests/digital_twin/personality**
  - Type: `suspicious_directory`
  - Directory matches suspicious pattern: personal

- **DigitalTwin/advanced-data-analysis-twin/tests/digital_twin/personality/test_personality_engine.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: personal

- **DigitalTwin/advanced-data-analysis-twin/tests/digital_twin/conversation/test_conversation_engine.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: conversation

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/README.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 101

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/README.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 173

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/connectors/social.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 1177

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/connectors/social.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 1178

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/connectors/email.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 41

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/connectors/email.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 51

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/processors/normalization.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 376

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/memory/procedural.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/memory/semantic.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/memory/index.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/memory/episodic.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/memory/system_enhanced.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/advanced-data-analysis-twin/digital_twin/personality**
  - Type: `suspicious_directory`
  - Directory matches suspicious pattern: personal

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/alignment.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/evolution.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/traits.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/models**
  - Type: `suspicious_directory`
  - Directory matches suspicious pattern: personal

- **DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/extractors**
  - Type: `suspicious_directory`
  - Directory matches suspicious pattern: personal

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/extractors/social.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/extractors/textual.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/extractors/activity.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/extractors/communication.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/personality/extractors/consumption.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/consciousness_mapper.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/predictive_engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/social_network.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/enhanced_quantum_profile.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/entanglement_matrix.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/recommendation_engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/temporal_analysis.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/trauma_archaeologist.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/reality_coherence.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/adapters/enhanced_temporal_analysis.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/evolution/enhanced_adaptive_engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/evolution/safety_validator.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/evolution/evolution_strategy_selector.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/evolution/ensemble_proposal_generator.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/evolution/adaptive_engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/conversation/analysis.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/digital_twin/conversation/context.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/examples/enhanced_digital_twin_example.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/examples/adaptive_evolution_example.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/examples/cognitive_twin_integration_example.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/api/middleware/auth.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 24

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/api/middleware/auth.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 25

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/api/middleware/auth.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 33

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/api/middleware/auth.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 33

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/api/middleware/auth.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 34

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/visualization/charts.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/visualization/dashboards.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/visualization/graphs.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/knowledge_graph/query.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/knowledge_graph/visualization.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/models/base.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 31

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/models/base.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 34

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/models/base.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 105

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/models/base.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 107

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/models/base.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 118

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/advanced/temporal.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/advanced/__init__.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/advanced/nlp.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/advanced/network.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/integrated_system/analysis/cognitive/personality.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: personal

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/cognitive/personality.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/cognitive/values.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/cognitive/memory.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/cognitive/__init__.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/cognitive/decision.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/communication/patterns.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/communication/__init__.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/integrated_system/analysis/communication/relationships.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: relationships?

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/analysis/communication/relationships.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/web/fastapi_integration.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 100

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/web/routes/web.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 258

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/social.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/calendar.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/email.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/integrated_system/data_processing/connectors/messages.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: messages?(?:_complete)?

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/messages.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 28

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 60

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 67

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 89

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 107

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/digital_twin/memory/system.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/digital_twin/memory/model.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/integrated_system/digital_twin/personality**
  - Type: `suspicious_directory`
  - Directory matches suspicious pattern: personal

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/digital_twin/personality/model.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/digital_twin/personality/engine.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/examples/data_import_example.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 353

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 30

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 32

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 53

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 55

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `name_field`
  - Found name_field pattern
  - Line: 75

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/pipeline/ingest.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/pipeline/serve.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/src/cognitive_twin/pipeline/export.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: export

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/pipeline/export.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/pipeline/analyze.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/core/utils.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/memory/vector_memory.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/src/cognitive_twin/memory/personality_memory.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: personal

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/memory/personality_memory.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/src/cognitive_twin/memory/conversation_memory.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: conversation

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/memory/conversation_memory.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/config/ai_config.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/config/settings.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/health/system_monitor.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/health/health_checker.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/models/cognitive.py**
  - Type: `personal_name`
  - Contains personal names: mom

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/realtime/streaming_analyzer.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/src/cognitive_twin/realtime/live_conversation.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: conversation

- **DigitalTwin/src/cognitive_twin/ai/conversation_ai.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: conversation

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/ai/conversation_ai.py**
  - Type: `personal_name`
  - Contains personal names: max

- **DigitalTwin/src/cognitive_twin/ai/personality_ai.py**
  - Type: `suspicious_filename`
  - Filename matches suspicious pattern: personal

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/ai/personality_ai.py**
  - Type: `personal_name`
  - Contains personal names: max

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/src/cognitive_twin/ai/analysis_ai.py**
  - Type: `personal_name`
  - Contains personal names: max

### MEDIUM (80)

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/pii_scan.py**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 60

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/pii_scan.py**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 106

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/pii_scan.py**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 106

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/pii_scan.py**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 107

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/tools/pii_scan.py**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 107

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/README.md**
  - Type: `email`
  - Found email pattern
  - Line: 278

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/CODE_OF_CONDUCT.md**
  - Type: `email`
  - Found email pattern
  - Line: 68

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/CODE_OF_CONDUCT.md**
  - Type: `email`
  - Found email pattern
  - Line: 94

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/CONTRIBUTING.md**
  - Type: `email`
  - Found email pattern
  - Line: 544

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/SECURITY.md**
  - Type: `email`
  - Found email pattern
  - Line: 28

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/HydraMind_v1/docs/SECURITY.md**
  - Type: `email`
  - Found email pattern
  - Line: 333

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `email`
  - Found email pattern
  - Line: 14

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `email`
  - Found email pattern
  - Line: 22

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `email`
  - Found email pattern
  - Line: 30

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `email`
  - Found email pattern
  - Line: 38

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_medium.json**
  - Type: `email`
  - Found email pattern
  - Line: 46

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `email`
  - Found email pattern
  - Line: 14

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `email`
  - Found email pattern
  - Line: 22

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `email`
  - Found email pattern
  - Line: 30

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `email`
  - Found email pattern
  - Line: 38

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/demo_small.json**
  - Type: `email`
  - Found email pattern
  - Line: 46

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/emails.json**
  - Type: `email`
  - Found email pattern
  - Line: 5

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/emails.json**
  - Type: `email`
  - Found email pattern
  - Line: 8

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/emails.json**
  - Type: `email`
  - Found email pattern
  - Line: 13

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/emails.json**
  - Type: `email`
  - Found email pattern
  - Line: 23

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/emails.json**
  - Type: `email`
  - Found email pattern
  - Line: 26

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/calendar_events.json**
  - Type: `email`
  - Found email pattern
  - Line: 12

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/calendar_events.json**
  - Type: `email`
  - Found email pattern
  - Line: 17

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/calendar_events.json**
  - Type: `email`
  - Found email pattern
  - Line: 34

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/calendar_events.json**
  - Type: `email`
  - Found email pattern
  - Line: 39

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/calendar_events.json**
  - Type: `email`
  - Found email pattern
  - Line: 44

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `email`
  - Found email pattern
  - Line: 7

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `email`
  - Found email pattern
  - Line: 15

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `email`
  - Found email pattern
  - Line: 23

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `email`
  - Found email pattern
  - Line: 31

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/fixtures/contacts.json**
  - Type: `email`
  - Found email pattern
  - Line: 39

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/aegistwin/demos/runner.py**
  - Type: `email`
  - Found email pattern
  - Line: 48

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/aegistwin/demos/runner.py**
  - Type: `email`
  - Found email pattern
  - Line: 49

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_data_connector_example.py**
  - Type: `email`
  - Found email pattern
  - Line: 356

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/README.md**
  - Type: `email`
  - Found email pattern
  - Line: 646

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/README.md**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 304

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/README.md**
  - Type: `apple_service`
  - Found apple_service pattern
  - Line: 336

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/README.md**
  - Type: `email`
  - Found email pattern
  - Line: 101

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/data_processing/README.md**
  - Type: `email`
  - Found email pattern
  - Line: 173

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/advanced-data-analysis-twin/api/middleware/auth.py**
  - Type: `email`
  - Found email pattern
  - Line: 26

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/engine.py**
  - Type: `email`
  - Found email pattern
  - Line: 200

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/engine.py**
  - Type: `email`
  - Found email pattern
  - Line: 201

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/core/engine.py**
  - Type: `email`
  - Found email pattern
  - Line: 362

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_data_processing.py**
  - Type: `email`
  - Found email pattern
  - Line: 38

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_data_processing.py**
  - Type: `email`
  - Found email pattern
  - Line: 225

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_data_processing.py**
  - Type: `email`
  - Found email pattern
  - Line: 233

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_data_processing.py**
  - Type: `email`
  - Found email pattern
  - Line: 261

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_data_processing.py**
  - Type: `email`
  - Found email pattern
  - Line: 265

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_helpers.py**
  - Type: `email`
  - Found email pattern
  - Line: 42

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_helpers.py**
  - Type: `email`
  - Found email pattern
  - Line: 43

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_helpers.py**
  - Type: `email`
  - Found email pattern
  - Line: 55

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/tests/test_helpers.py**
  - Type: `email`
  - Found email pattern
  - Line: 56

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/social.py**
  - Type: `email`
  - Found email pattern
  - Line: 791

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/calendar.py**
  - Type: `email`
  - Found email pattern
  - Line: 177

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/calendar.py**
  - Type: `email`
  - Found email pattern
  - Line: 185

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/calendar.py**
  - Type: `email`
  - Found email pattern
  - Line: 185

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/calendar.py**
  - Type: `email`
  - Found email pattern
  - Line: 188

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/data_processing/connectors/calendar.py**
  - Type: `email`
  - Found email pattern
  - Line: 199

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `email`
  - Found email pattern
  - Line: 61

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `email`
  - Found email pattern
  - Line: 68

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `email`
  - Found email pattern
  - Line: 90

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `email`
  - Found email pattern
  - Line: 108

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/api_documentation.md**
  - Type: `email`
  - Found email pattern
  - Line: 121

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/docs/user_guide.md**
  - Type: `email`
  - Found email pattern
  - Line: 327

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/examples/data_import_example.py**
  - Type: `email`
  - Found email pattern
  - Line: 174

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/examples/data_import_example.py**
  - Type: `email`
  - Found email pattern
  - Line: 175

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/examples/data_import_example.py**
  - Type: `email`
  - Found email pattern
  - Line: 176

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/examples/data_import_example.py**
  - Type: `email`
  - Found email pattern
  - Line: 185

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/examples/data_import_example.py**
  - Type: `email`
  - Found email pattern
  - Line: 186

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `email`
  - Found email pattern
  - Line: 54

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `email`
  - Found email pattern
  - Line: 76

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/users.py**
  - Type: `email`
  - Found email pattern
  - Line: 100

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/data.py**
  - Type: `email`
  - Found email pattern
  - Line: 33

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/data.py**
  - Type: `email`
  - Found email pattern
  - Line: 90

- **/Users/nicholastoledo/CascadeProjects/AegisTwin/DigitalTwin/integrated_system/api/endpoints/data.py**
  - Type: `email`
  - Found email pattern
  - Line: 115


---
## Recommended Actions

1. Move all flagged files to `/graveyard/PII/`
2. Add paths to `.gitignore`
3. Generate synthetic replacements where needed
4. Re-run this scanner to verify cleanup
5. Use `git filter-repo` to purge history if needed
