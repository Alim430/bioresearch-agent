> **DRAFT — not submitted to arXiv yet.** This file is the working source of truth for a future arXiv submission. It is intentionally *not* referenced by the README and is *not* part of the v1.0.0 release narrative.

# arXiv Abstract — BioResearch Agent Framework

## Title

**BioResearch Agent: A Tool-First Multi-Agent Framework for Biomedical Research Automation**

## Abstract

We present the **BioResearch Agent Framework**, a runnable and LLM-agnostic system for automating end-to-end biomedical research workflows.

Unlike prior work that focuses on isolated tasks such as literature retrieval or single-step reasoning, our framework introduces a **tool-first agent architecture** that enables structured execution of complete biomedical research pipelines, from hypothesis formulation to publication-ready outputs.

The system is built around six modular research engines that operate over a 12-stage biomedical research lifecycle, including literature synthesis, statistical analysis, biomarker discovery, causal inference, and scientific writing. These engines are decoupled from any specific large language model and instead exposed as standardized tools callable via CLI, Python SDK, or external LLM agents.

We further introduce a plugin-based biomedical data layer integrating widely used resources such as PubMed, GEO, and GWAS summary statistics. All workflows produce structured scientific artifacts including reports, figures, knowledge graphs, and bibliographic references.

Empirical evaluation across three representative biomedical tasks — literature review, biomarker discovery, and Mendelian randomization — demonstrates that the system can substantially reduce manual effort while maintaining reproducible scientific outputs.

The BioResearch Agent Framework provides a unified and extensible infrastructure for LLM-driven scientific discovery in biomedicine.

## Keywords

Biomedical AI, LLM Agents, Scientific Workflows, Bioinformatics, Tool-Augmented LLMs, Research Automation, Mendelian Randomization, Multi-Agent Systems

## Target Venues

- arXiv (cs.AI, q-bio.QM)
- NeurIPS / ICML AI for Science Workshop
- Nature Methods (if extended with real experimental validation)

## Author Affiliation Template

[Your Name]¹, [Co-author Name]²
¹ Shanghai University of Traditional Chinese Medicine, Affiliated Municipal Hospital of TCM
² [Institution]

*Corresponding author: [email]*
