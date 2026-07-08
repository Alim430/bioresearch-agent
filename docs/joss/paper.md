---
title: 'BioResearch Agent Framework: A Reproducible Workflow Framework for Biomedical Analysis'
tags:
  - bioinformatics
  - reproducibility
  - workflow
  - mendelian-randomization
  - agent-skills
authors:
  - name: Alimujiang Tudiyusufu
    affiliation: "1, 2"
    orcid: ""   # TODO: fill your ORCID before submission
affiliations:
  - name: Shanghai University of Traditional Chinese Medicine
    index: 1
  - name: Institute of Basic Medical Sciences, Peking Union Medical College
    index: 2
date: 8 July 2026
bibliography: paper.bib
---

# Summary

BioResearch Agent Framework is an open-source, reproducible workflow framework that integrates
three core biomedical analysis pipelines — literature review, biomarker discovery, and
Mendelian randomization — behind a single, standardized execution engine. It exposes the same
engine through four access layers (CLI, Python SDK, API contract, and Agent Skills), so the
workflows can be invoked either directly by a researcher or by an AI assistant through a
standardized skill interface.

The framework's contribution is a **reproducible execution contract**, not a new algorithm: it
delegates all statistics to established domain libraries (t-test + Bonferroni correction for
differential expression, hypergeometric testing for pathway enrichment, and inverse-variance
weighted two-sample Mendelian randomization). Every run emits data-derived tables, statistical
results, and figures rather than free-text summaries.

# Statement of need

Reproducible computational workflows in biomedicine are typically encoded either as
pipeline-specific languages (e.g., Nextflow [@nextflow], Snakemake [@snakemake]) or as manual
scripts. Meanwhile, AI assistants are increasingly expected to *perform* analysis, yet most can
only generate plausible-looking code or prose. There is a gap between (a) validated biomedical
tools and (b) agent environments that researchers actually use. BioResearch Agent Framework fills
that gap by packaging existing tools behind a unified, auditable interface that an agent — or a
human — can invoke to produce real, reproducible outputs.

# State of the field

Nextflow and Snakemake solved portable pipeline execution; Galaxy solved browser-based access;
limma [@limma] and TwoSampleMR [@twosamplemr] solved specific statistical tasks. What remains
under-served is a **thin, tool-agnostic execution layer** that (i) standardizes inputs/outputs
across heterogeneous biomedical workflows and (ii) is loadable as an Agent Skill so that AI
assistants dispatch to validated code instead of hallucinating analysis. BioResearch Agent
Framework targets exactly this interface layer.

# Positioning

Unlike autonomous "AI scientist" systems, BioResearch Agent Framework makes no reasoning claims.
It is deliberately a **workflow execution framework with an agent-compatible interface**: skills
are invocation wrappers, and all computation runs in the underlying modules. This keeps the
system honest, auditable, and citable as software infrastructure.

# Architecture

- **Workflow layer** — `literature`, `biomarker`, `causal` (extensible).
- **Processing modules** — question → retrieval → analysis → evidence → narrative → execution.
- **Access layer** — CLI (`bioresearch run …`), Python SDK (`from bioresearch import Agent`),
  API contract (`bioresearch/toolspec.json`), and Agent Skills (`skills/`, conforming to the
  open Agent Skills standard).
- **Execution** — stages 1–8 (question → hypothesis → literature → design → data → stats →
  bioinformatics → output) are implemented; stages 9–12 are conceptual extensions.

A `bioresearch doctor` command validates environment, dependencies, network access, and output
permissions, supporting reproducible runs.

# Documentation

Documentation lives in the repository README, `skills/README.md` (capability map and agent
installation), and `examples/` (copy-paste agent workflows). The `skills/registry.json` provides
a machine-readable inventory of active and planned skills.

# Acknowledgements

We acknowledge the developers of the underlying open-source biomedical libraries that this
framework dispatches to.

# References
