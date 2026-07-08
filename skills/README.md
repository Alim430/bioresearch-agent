# BioResearch Agent Skills

Reusable **Agent Skills** that give AI assistants (Claude, Cursor, Codex, and other
Agent Skills–compatible clients) the ability to run real biomedical research workflows through
the BioResearch Agent framework.

> Skills are an **interface layer, not a reasoning layer**. Each skill is a thin wrapper that
> dispatches to the framework's `bioresearch` CLI — it adds no analysis of its own. Your assistant
> gains *execution* ability (real DEG / MR / literature pipelines), not autonomous scientific
> reasoning.

---

## Supported clients

| Client | Skill directory |
|:---|:---|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/skills/` |
| Claude Desktop / CLI (Linux) | `~/.config/claude/skills/` |
| Cursor | `~/.cursor/skills/` |
| Codex / generic | `~/.config/agent/skills/` |

---

## Capability map

Skills are organized by group. All `active` skills map to a real `bioresearch` entry point.

### `core/` — framework & validation

| Skill | Capability | Trigger |
|:---|:---|:---|
| `bioresearch-introduction` | Framework overview & capability map | "what can BioResearch Agent do" |
| `bioresearch-environment-check` | Environment / reproducibility validation (`bioresearch doctor`) | "validate environment / troubleshoot" |
| `bioresearch-agent-router` | Rule-based intent → workflow (deterministic, no LLM) | "classify / route a research intent" |

### `biomedical/` — research workflows

| Skill | Capability | Trigger |
|:---|:---|:---|
| `bioresearch-literature-analysis` | Literature review + co-occurrence knowledge graph | "literature review / research gaps" |
| `bioresearch-biomarker-discovery` | Biomarker discovery (DEG + enrichment + ranking) | "find biomarkers for a disease" |
| `bioresearch-differential-expression` | Differential expression (DEG) | "differential expression / volcano plot" |
| `bioresearch-pathway-enrichment` | Pathway / GO / KEGG enrichment | "pathway / GO enrichment" |
| `bioresearch-causal-inference` | Two-sample Mendelian randomization (IVW + sensitivity) | "causal effect / MR" |
| `bioresearch-causal-evidence` | Causal-evidence chain (coloc → TWAS → fine-map → MR) | "causal evidence / colocalization / TWAS" |
| `bioresearch-disease-case-study` | Real-data disease case study + blind benchmark | "case study / validation / benchmark" |

> **Note on granularity:** `differential-expression` and `pathway-enrichment` are focused entry
> points that invoke the same `biomarker` workflow (DEG is stage 1, enrichment is stage 2). There
> is no separate CLI command for them — the skills exist so an agent fires the right workflow when
> the user's intent is specifically DEG or enrichment.

---

## Install

### Recommended — installer (detects your client)

```bash
./skills/install.sh
```

The installer copies all `active` skills into your agent's skill directory and verifies the
framework with `bioresearch doctor`.

### Manual — Claude Desktop (macOS)

```bash
cp -r skills/core/project-introduction \
      skills/core/environment-check \
      skills/biomedical/literature-analysis \
      skills/biomedical/biomarker-discovery \
      skills/biomedical/differential-expression \
      skills/biomedical/pathway-enrichment \
      skills/biomedical/causal-inference \
      skills/biomedical/causal-evidence \
      "$HOME/Library/Application Support/Claude/skills/"
```

### Manual — Cursor / Codex / generic

Replace the target with `~/.cursor/skills/` or `~/.config/agent/skills/`.

Restart the client after copying. See the parent [README](../README.md#-workflow-skills) for the
full workflow reference.

---

## How it works

```
Your AI assistant
      │  (loads a skill from skills/)
      ▼
Skill (SKILL.md)  ── dispatches to ──▶  bioresearch CLI
      │                                      │
      │                                      ▼
      │                            Reproducible workflow modules
      │                            (PubMed · GEO · KEGG/GO · IVW-MR)
      ▼
Data-derived outputs (tables, figures, reports)
```

No skill contains code that makes network calls itself — all execution happens in the framework.

---

## Roadmap (planned — not yet shipped as loadable skills)

These capabilities are on the roadmap but have **no implementation in the current release**. They
are listed here for transparency and are intentionally *not* shipped as loadable `SKILL.md` files,
to avoid advertising capabilities the framework does not yet have.

- `bioresearch-workflow-orchestration` — multi-workflow orchestration (literature → biomarker → causal)
- `bioresearch-single-cell-analysis`
- `bioresearch-spatial-transcriptomics`
- `bioresearch-protein-analysis`
- `bioresearch-clinical-data-analysis`

The machine-readable list (with `status` flags) is in [`registry.json`](registry.json).

---

## Honesty note

BioResearch Agent executes **reproducible workflows** by dispatching to existing domain libraries
(limma-style DEG, hypergeometric enrichment, TwoSampleMR-style IVW). It does **not** reason about
biology and does **not** discover novel science on its own. Skills extend assistants with
*execution*, not intelligence.
