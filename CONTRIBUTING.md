# Contributing to BioResearch Agent Framework

Thanks for your interest in improving reproducible biomedical workflows.

## Scope

This repository is a **reproducible workflow framework with agent-compatible skill interfaces** — it executes literature analysis, biomarker discovery, and causal-inference pipelines through standardized, auditable interfaces over existing domain tools (PubMed, GEO, KEGG/GO, limma, GSEA, TwoSampleMR). It is **not** an autonomous research agent and makes no discovery claims of its own.

Contributions should keep that boundary intact:

- ✅ New workflows, processing modules, skills, benchmarks, or docs.
- ✅ Honest evidence grading (A/B = real public data; C = synthetic/offline methodology).
- ❌ Claims that the framework "discovers biology" or "reasons autonomously".
- ❌ Introduction of controlled-access or individual-level datasets (MetaBrain, UKB-PPP, ADNI, deCODE). See `DATA_GOVERNANCE.md`.

## How to contribute

1. Fork and clone.
2. Create a feature branch: `git checkout -b feat/your-change`.
3. Follow the coding standards (numbered file system, `pathlib`/`here` path management, fixed seeds, Conventional Commits). A cross-project rule set is loaded automatically if you use the `bioinfo-code-style` skill.
4. Add or update a validation case under `bio-research-os/eval/` with a reproducible Evidence Package (commit + environment + data `sha256`).
5. Run `bioresearch doctor` and the relevant eval case locally.
6. Open a PR describing the change, the evidence grade, and how to reproduce.

## Evidence honesty

Every result must state its evidence grade. Low recovery (e.g. Mendelian PD drivers in bulk tissue) is reported, not hidden. Do not fabricate DOIs, statistics, or preprint links.

## Code of conduct

Be respectful; keep discussions focused on reproducible, auditable science.
