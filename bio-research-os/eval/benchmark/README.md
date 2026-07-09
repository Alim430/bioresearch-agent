# Benchmark-Lite: 20-Task Regression Suite

A deterministic, network-free regression suite that verifies the core contracts of BioResearch Agent v1.5 still hold after code changes.

## Quick Start

```bash
# Standalone (no pytest needed)
python tests/benchmark_lite.py

# Or with pytest
pytest tests/benchmark_lite.py -v
```

## What It Tests

The 20 tasks are organised into six groups:

| Group | Tasks | Scope |
|:---|:---|:---|
| **A — Router** | 1–8 | Intent classification for all 5 routes + unknown, determinism, command mapping |
| **B — Core State** | 9–11 | Stage enum (12 stages), EvidenceGrade enum (A–E), ResearchState initialization & serialization |
| **C — Engines** | 12–17 | Each of the 6 Layer-2 engines in isolation: Question, Retrieval, Analysis, Evidence, Narrative, Execution |
| **D — Pipeline** | 18 | Full 6-engine chain from IDEATION to PUBLICATION |
| **E — Registry** | 19 | `skills/registry.json` has 10 active skills with correct structure |
| **F — Manifest + Governance** | 20 | `eval/manifest.json` has 6 implemented cases; `.gitignore` excludes raw data |

## Design Principles

1. **No network, no external data, no LLM API key.** All engine tests use `mock_mode=True` with a fixed seed (`random.seed(42)`) for reproducibility.
2. **Structural assertions, not value assertions.** Because mock engines use random, the benchmark checks that the right keys exist, types are correct, and invariants hold — not that specific numbers match.
3. **Deterministic where it matters.** The router is fully deterministic (no randomness). Registry and manifest tests read JSON files and validate structure.
4. **Pytest-compatible but not pytest-dependent.** Each task is a standalone function that can be called directly or collected by pytest.

## Task Inventory

### Group A — Router (8 tasks)

| # | Task | Asserts |
|:--|:---|:---|
| 01 | `biomarker_routing` | GEO + DEG keywords route to "biomarker" |
| 02 | `causal_routing` | MR keywords route to "causal" |
| 03 | `literature_routing` | Literature review keywords route to "literature" |
| 04 | `doctor_routing` | Environment check keywords route to "doctor" |
| 05 | `case_study_routing` | Case study keywords route to "case-study" |
| 06 | `unknown_intent` | Unrecognised intent returns "unknown" with suggestion list |
| 07 | `router_determinism` | Same input produces identical output |
| 08 | `route_to_command` | Every route maps to a non-empty CLI string |

### Group B — Core State (3 tasks)

| # | Task | Asserts |
|:--|:---|:---|
| 09 | `stage_enum` | 12 stages, values 1–12, IDEATION=1, PUBLICATION=12 |
| 10 | `evidence_grade_enum` | 5 grades A–E |
| 11 | `research_state_init` | Default values, run_id auto-generated, to_dict serialization |

### Group C — Engines (6 tasks)

| # | Task | Engine | Asserts |
|:--|:---|:---|:---|
| 12 | `question_engine` | QuestionEngine | Hypothesis with falsifiability criteria, confidence in [0,1] |
| 13 | `retrieval_engine` | RetrievalEngine | ≥5 papers, ≥1 dataset, QC report with required keys |
| 14 | `analysis_engine` | AnalysisEngine | Statistical/bioinformatics/causal results with required keys |
| 15 | `evidence_engine` | EvidenceEngine | Grades, conflict report, aggregate confidence in [0,1] |
| 16 | `narrative_engine` | NarrativeEngine | IMRAD sections, ≥1 figure, ≥1 table |
| 17 | `execution_engine` | ExecutionEngine | Review report, submission materials, accept probability in [0,1] |

### Group D — Pipeline (1 task)

| # | Task | Asserts |
|:--|:---|:---|
| 18 | `full_pipeline` | All 6 engines chained: IDEATION → PUBLICATION, each engine feeds the next |

### Group E — Registry (1 task)

| # | Task | Asserts |
|:--|:---|:---|
| 19 | `skills_registry` | 10 active skills, correct structure (name/path/group/capability/triggers/status), expected skill names |

### Group F — Manifest + Governance (1 task)

| # | Task | Asserts |
|:--|:---|:---|
| 20 | `manifest_and_governance` | 6 implemented cases in manifest, evidence grades present, .gitignore excludes *.txt.gz / *.gct.gz / raw/ |

## Exit Codes

- **0**: All 20 tasks passed
- **1**: One or more tasks failed (details printed to stdout)
