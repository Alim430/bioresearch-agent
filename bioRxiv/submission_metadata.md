# BioRxiv Submission Metadata — BioResearch Agent

> Copy-paste ready fields for the bioRxiv submission web form.
> Manuscript to upload: `manuscript.pdf` (compiled from `source/`, content already aligned with this metadata).
> bioRxiv performs only basic scope/completeness screening — **no endorsement required** (unlike arXiv).

---

## Title (must match the uploaded PDF)

**BioResearch Agent: A Tool-First Framework for Structured Biomedical Research Workflows**

> ⚠️ Title note: the compiled PDF uses the wording above. If you prefer the alternate wording
> *"A Reproducible Workflow Framework for Biomedical Analysis Pipelines"* (the version in
> `../arxiv-abstract.md`), you must recompile `source/main.tex` — no LaTeX toolchain was available
> in this environment, so the existing PDF was used as-is. Exact edit is in
> `bioRxiv_submission_guide.md` §"Title consistency".

---

## Authors

1. **Alimujiang Tudiyusufu**
   - Affiliation: *Independent Researcher*
     - Optionally update to an institutional affiliation if applicable, e.g.
       *Institute of Basic Medical Sciences, Peking Union Medical College, Chinese Academy of Medical Sciences, Beijing, China*
       (confirm before changing — the PDF currently states "Independent Researcher").
   - Email: **almj@ibms.pumc.edu.cn** (use your bioRxiv account email; the PDF shows `Alim_T@foxmail.com`)
   - ORCID: **0009-0002-5180-6226**

---

## Abstract

BioResearch Agent is an open-source, reproducible workflow framework for structured biomedical research. It integrates three common analysis pipelines—literature review, biomarker discovery, and Mendelian randomization—behind a unified command-line interface, Python SDK, and external API invocation contract. The system emphasizes reproducible execution through version-pinned dependencies, fixed random seeds, and continuous integration across Python 3.9–3.12. A lightweight standardized interface provides a consistent entry point for external systems to invoke workflows without modifying core pipeline code. All workflows are validated via automated tests and produce standardized structured outputs, including statistical tables, co-occurrence graphs, and formatted figures. The framework is released as a frozen snapshot with archived commits and is intended as a reusable infrastructure layer rather than a replacement for domain-specific analysis tools. We emphasize that the primary contribution of this work is not algorithmic novelty, but the design of a reproducible execution contract that standardizes how existing biomedical analysis tools are invoked, composed, and validated across heterogeneous environments.

---

## Keywords

Biomedical analysis, workflow framework, reproducibility, standardized interface, literature review, biomarker discovery, Mendelian randomization, bioinformatics

---

## Subject areas (bioRxiv dropdown)

- **Primary:** `Bioinformatics`
- **Secondary:** `Genetics`
- **Secondary:** `Genomics`
  - (alternative secondary if preferred: `Systems Biology`)

---

## Preprint category

`Tools and Resources`  *(best fit — a reusable framework/software; "Methods" is an acceptable alternative)*

---

## License

`CC-BY` (bioRxiv default). `CC0` also available if you prefer maximum reuse.

---

## Code availability

https://github.com/Alim430/bioresearch-agent

---

## Author contributions

A.T. conceived the framework, implemented the workflow engine and interfaces, validated outputs, and wrote the manuscript.

---

## Competing interests

The author declares no competing interests.

---

## Funding

No specific funding was received for this work. *(edit if applicable)*

---

## Screening expectation

bioRxiv screens for scope (life-sciences relevance) and completeness only. Posting typically completes in **< 48 h** and a **DOI** is assigned on posting. No endorsement step.
