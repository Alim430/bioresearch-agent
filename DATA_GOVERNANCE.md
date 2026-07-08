# Data Governance & Access Policy

This document defines what data **BioResearch Agent** is allowed to touch, download, cache, or
commit. It exists because the project is a **public** repository and some biomedical datasets
carry individual-level or controlled-access restrictions.

> **One-line rule:** the framework only processes **public, de-identified, or summary-level**
> data. **Controlled-access / individual-level datasets are out of scope** and must never be
> added to this repository. Derived analysis results from any other project are also excluded.

---

## 1. Data tiers

| Tier | Examples | May the framework use it? | May it be committed to this repo? |
|:---|:---|:---|:---|
| **Public open-access** | GEO, GTEx eQTL summary, PsychENCODE, eQTLGen, FinnGen summary, GWAS Catalog / IEU summary, PubMed, KEGG/GO, SEA-AD (AMP-AD open tier), Allen Brain Cell Atlas, CZ cellxgene | ✅ Yes | ✅ Only derived/summary outputs the framework itself produces (CSV/figures/evidence packages); **never the raw source files** |
| **Summary-level but registration-gated** | FinnGen (registration), eQTLGen (registration) | ✅ Yes (user supplies locally) | ❌ No raw files |
| **Controlled-access / individual-level** | MetaBrain, UKB-PPP, ADNI, deCODE pQTL, UK Biobank individual-level | ❌ **No** | ❌ **Never** |
| **Derived results of another project** | Another project's `processed/`, `structure/`, CellOracle networks, figures | ❌ No (not this framework's output) | ❌ No |

---

## 2. What the framework actually accesses

Per the README "Data & Network Access" section, the framework's network calls are:

- **Literature** → PubMed (NCBI E-utilities), read-only
- **Biomarker** → GEO (NCBI), KEGG, GO, read-only
- **Causal / Causal-evidence** → GWAS / eQTL **summary statistics**, read-only (simulated by default)

There is **no telemetry** and **no external write access**. All synthetic fallbacks run fully
offline with a fixed seed.

---

## 3. v1.5 real-data plan (safe path)

The causal-evidence chain (GWAS → eQTL → colocalization → TWAS → fine-mapping → MR) will be
validated on **real public summary statistics only**:

- **GWAS (trait = Alzheimer's):** Jansen 2019 (IGAP/GR@P), Wightman 2021 (PGC ALZ),
  Bellenguez 2022, or FinnGen R13 AD endpoints — all public summary stats.
- **eQTL (tissue = brain):** **GTEx v8** (`Brain_Cortex`, `Brain_Hippocampus`, …) or
  **PsychENCODE** — both public. *Not* MetaBrain.

These are supplied to the workflow via local file paths (`--gwas-path` / `--eqtl-path`); they are
**loaded, not copied** into the repo. The workflow emits only derived CSV / figures / an Evidence
Package — never the raw inputs.

**Explicitly excluded from v1.5 real-data:** MetaBrain, UKB-PPP, ADNI, deCODE — controlled-access.

---

## 4. Repository hygiene (enforced)

`.gitignore` excludes raw downloads so they cannot be committed by accident:

```
*.txt.gz  *.tsv.gz  *.csv.gz  *.h5ad  *.h5  *.rds  *.mtx  *.gct.gz
raw/  data/raw/  eval/data/  downloads/
```

Before any commit, confirm no controlled-access or raw individual-level file is staged.

---

## 5. Appendix — inventory of a local AD-VCP data folder (`ad-paper2` / `ad-vcp-data`)

For transparency, here is the classification of datasets found in the user's separate AD-VCP
project folder. **Nothing from the "Excluded" rows may be reused or committed by this framework.**

### Reusable (public source — not AD-VCP's own results)

| Source | Type | Tier | Reuse? |
|:---|:---|:---|:---|
| Jansen 2019 AD GWAS (`AD_sumstats_…`) | GWAS summary | Public (IEU/GWAS Catalog) | ✅ |
| Wightman 2021 PGC ALZ (`PGCALZ2…`) | GWAS summary | Public (PGC) | ✅ |
| Bellenguez 2022 (`GCST90027158`) | GWAS summary | Public (GWAS Catalog) | ✅ |
| FinnGen R13 AD endpoints (`finngen_R13_AD_…`) | GWAS summary | Public (registration) | ✅ |
| GTEx v8 eQTL (incl. `Brain_Cortex`, `Brain_Hippocampus`) | eQTL summary | Public | ✅ |
| PsychENCODE | eQTL/expression | Public | ✅ |
| eQTLGen | eQTL summary | Public (registration) | ✅ (optional) |
| GEO: GSE134578, GSE147528, GSE164823, GSE174367, GSE178317, GSE181279, GSE200218, GSE220442 | bulk / scRNA / spatial | Public | ✅ (new case inputs) |
| SEA-AD microglia `.h5ad` (AMP-AD) | single-cell | Public (open tier) | ✅ (future single-cell) |
| Allen Brain Cell Atlas | single-cell | Public | ✅ (future) |
| CZ cellxgene census | single-cell | Public | ✅ (future) |
| CRISPR Perturb-seq (GSE178317) | perturbation scRNA | Public | ✅ (future) |

### Excluded — controlled-access (privacy + license)

| Source | Why excluded |
|:---|:---|
| MetaBrain eQTL | Controlled-access, individual-level brain RNA-seq; DUA; re-identification risk |
| UKB-PPP | UK Biobank controlled access |
| ADNI v5.1 | ADNI data-use agreement |
| deCODE pQTL | Proprietary/controlled terms (conservative exclusion) |

### Excluded — AD-VCP derived analysis results (per user constraint)

| Path | Why excluded |
|:---|:---|
| `data/processed/` | AD-VCP's own processed derivatives |
| `data/structure/` | AD-VCP virtual-cell structure outputs |
| `celloracle_data/` | AD-VCP CellOracle regulatory networks |
| `figures/`, `results/` | AD-VCP visualizations / outputs |

> **Boundary:** reusing a *public source input* (e.g., GTEx eQTL, Jansen GWAS) is fine — those are
> not AD-VCP's intellectual property. Reusing AD-VCP's *derived outputs* above is not.
