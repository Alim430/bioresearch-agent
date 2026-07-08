# Cover Letter / Submission Statement — BioResearch Agent

> **bioRxiv does NOT require a cover letter** — this file is provided for your records and for
> reuse if you later submit the work to a journal (e.g., JOSS, or a domain journal). It is written
> to match the honest, defensible framing used throughout the manuscript: a *reproducible workflow
> framework with a standardized multi-interface access layer*, **not** an autonomous reasoning system.

---

**To the Editor,**

We submit a preprint describing **BioResearch Agent**, an open-source, reproducible workflow
framework that integrates three common biomedical analysis pipelines — literature review,
biomarker discovery, and Mendelian randomization — behind a unified command-line interface,
Python SDK, API contract, and agent-skill interface.

The contribution is explicitly **not algorithmic novelty**. It is the design of a reproducible
execution contract: version-pinned dependencies, fixed random seeds, and continuous integration
that standardize how existing biomedical analysis tools (e.g., PubMed retrieval, differential
expression with t-test + Bonferroni correction, two-sample Mendelian randomization via IVW) are
invoked, composed, and validated across heterogeneous environments. The agent-skill interface
exposes this engine to AI assistants as an *execution* layer — it grants the assistant the ability
to run real analyses, not to reason about biology autonomously.

We believe this work is of interest to the bioinformatics and computational-biology communities,
and to researchers building AI-assisted research tooling, because it lowers the barrier to
reproducible, composable biomedical workflows and provides a concrete pattern for connecting
agent environments to validated scientific pipelines.

The manuscript is original, not under consideration elsewhere, and all code and frozen release
snapshots are publicly available at https://github.com/Alim430/bioresearch-agent.

Sincerely,
Alimujiang Tudiyusufu
ORCID: 0009-0002-5180-6226
almj@ibms.pumc.edu.cn
