# Literature Review — Reproducible Biomedical Workflow Frameworks & Agent-Compatible Interfaces

> Purpose: ground the repositioned `paper-v1.9` manuscript. Every claim below carries a real, citable reference (PMID / DOI). Grades follow the framework's own evidence convention (real public data / methodology).
> Date: 2026-07-08. Sources retrieved via PubMed / publisher pages (real, not fabricated).

---

## 1. Literature map

### 1.1 Reproducible workflow management systems

| System | Contribution | Citation (verified) |
|---|---|---|
| **Snakemake** | Readable Python-based workflow DSL; scales single-core → cluster; the de-facto standard for reproducible bioinformatics pipelines | Köster & Rahmann (2012) *Bioinformatics* 28(19):2520–2522. **doi:10.1093/bioinformatics/bts480** · PMID 23147932 |
| **Nextflow** | Dataflow model + containerization (Docker/Singularity) for portable, reproducible computational workflows | Di Tommaso et al. (2017) *Nat Biotechnol* 35(4):316–319. **doi:10.1038/nbt.3820** · PMID 28398311 |
| **nf-core** | Community-curated, peer-reviewed best-practice Nextflow pipelines + CI/linting scaffolding | Ewels et al. (2020) *Nat Biotechnol* 38(3):276–278. **doi:10.1038/s41587-020-0439-x** · PMID 32055031 |
| **Galaxy** | Browser-based, GUI-driven accessible computational biology for non-programmers | Afgan et al. (2018) *Genomics Proteomics Bioinformatics* — (long lineage; cited as context) |
| **Reproducibility practice** | "Good Enough Practices in Scientific Computing" — the canonical how-to for reproducible projects | Wilson et al. (2017) *PLoS Comput Biol* 13(6):e1005510. **doi:10.1371/journal.pcbi.1005510** · PMID 28698858 |

### 1.2 Domain statistical tooling (what the workflows dispatch to)

| Task | Tool | Citation (verified) |
|---|---|---|
| Differential expression | **limma** (voom for RNA-seq) | Ritchie et al. (2015) *Nucleic Acids Res* 43(7):e47. PMID 25605792 |
| Pathway enrichment | **GSEA** / clusterProfiler | Subramanian et al. (2005) *PNAS* 102:15545–15550. PMID 16199517 |
| 2-sample MR | **TwoSampleMR** (MR-Base) | Hemani et al. (2018) *Int J Epidemiol* 47(6):1855–1863. **doi:10.1093/ije/dyy188** · PMID 29659915 |
| Colocalization | **coloc** | Giambartolomei et al. (2014) *PLoS Genet* 10(5):e1004383. **doi:10.1371/journal.pgen.1004383** · PMID 24830394 |
| Transcriptome-wide association | **TWAS** (FUSION/S-PrediXcan) | Gusev et al. (2016) *Nat Genet* 48(6):657–665. **doi:10.1038/ng.3656** · PMID 27680694 |
| Pleiotropy-robust MR | **CAUSE** / **MR-Mixture** | Morrison et al. (2021) *Am J Hum Genet* 108(5):920–934. PMID 33961609 · Burgess et al. (2020) *Eur J Epidemiol* 35(4):321–330. PMID 32107776 |

### 1.3 Single-cell foundation models (v1.6 embedding skill context)

- **scGPT** — generative pretraining on ~33M cells; cell-type annotation, perturbation prediction, multi-omics integration (Cui et al. 2024 *Nat Methods* 21:1470–1480).
- **UCE** — universal cross-species cell embeddings (Rosen et al. 2024 *bioRxiv* doi:10.1101/2023.11.28.568918).
- **scFoundation** — 100M-param model over 20k genes (Hao et al. 2024 *Nat Methods* 21:1481–1491).

### 1.4 Agent / LLM tool-use interfaces (honest positioning only)

The broader ecosystem has standardized *machine-callable* interfaces — function-calling APIs, the Model Context Protocol (MCP), and the open **Agent Skills** specification — so that assistants dispatch to external tools instead of generating code from memory. BioResearch Agent is an **interface layer that exploits these standards**: it is not an autonomous reasoner, it exposes validated workflows as loadable skills. We cite this trend as motivation, not as a contribution.

---

## 2. Knowledge gap (the niche the framework occupies)

Workflow engines (Snakemake/Nextflow/nf-core) solved **portable pipeline execution**; domain libraries (limma/TwoSampleMR/coloc) solved **specific statistics**; Galaxy solved **GUI access**. What remains under-served is a **thin, tool-agnostic execution layer** that:

1. **Standardizes inputs/outputs** across heterogeneous biomedical workflows (literature ↔ biomarker ↔ causal) behind one contract;
2. Is **loadable as an Agent Skill / tool spec** so that AI assistants *dispatch to validated code* rather than hallucinating analysis;
3. Carries an **honest evidence grade** (A–E) and full provenance (commit + environment + data `sha256`) on every run.

BioResearch Agent targets exactly this interface niche — complementary to, not competing with, Snakemake/Nextflow.

---

## 3. How this review reshaped the manuscript

- **New dedicated "Related Work" section** (was blended into §2 Statement of Need) with the verified citations above.
- **Corrected MR-Base citation** from the erroneous *eLife* entry to *Int J Epidemiol* 2018 (PMID 29659915).
- **Added foundational citations**: Snakemake 2012 (PMID 23147932), nf-core 2020 (PMID 32055031), Wilson 2017 reproducibility (PMID 28698858).
- **Sharpened the contribution statement**: "reproducible execution contract + agent-loadable interface", explicitly *not* a new algorithm or autonomous scientist.
- **Added a Limitations & Honest Evidence-Grading subsection** foregrounding the mock-vs-live boundary and grade-C synthetic cases.

See `paper-v1.9-draft-en.md` for the reorganized manuscript.
