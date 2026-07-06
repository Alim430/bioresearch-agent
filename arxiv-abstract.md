> **arXiv submission abstract — aligned with the system paper.** This file mirrors the submitted title and abstract; it is consistent with `README.md` and the paper source under `docs/`.

# arXiv Abstract — BioResearch Agent Framework

## Title

**BioResearch Agent: A Reproducible Workflow Framework for Biomedical Analysis Pipelines**

## Abstract

BioResearch Agent is an open-source, reproducible workflow framework for structured biomedical research. It integrates three common analysis pipelines—literature review, biomarker discovery, and Mendelian randomization—behind a unified command-line interface, Python SDK, and external API invocation contract. The system emphasizes reproducible execution through version-pinned dependencies, fixed random seeds, and continuous integration across Python 3.9–3.12. A lightweight standardized interface provides a consistent entry point for external systems to invoke workflows without modifying core pipeline code. All workflows are validated via automated tests and produce standardized structured outputs, including statistical tables, co-occurrence graphs, and formatted figures. The framework is released as a frozen snapshot with archived commits and is intended as a reusable infrastructure layer rather than a replacement for domain-specific analysis tools. We emphasize that the primary contribution of this work is not algorithmic novelty, but the design of a reproducible execution contract that standardizes how existing biomedical analysis tools are invoked, composed, and validated across heterogeneous environments.

## Keywords

Biomedical analysis, workflow framework, reproducibility, standardized interface, literature review, biomarker discovery, Mendelian randomization, bioinformatics
