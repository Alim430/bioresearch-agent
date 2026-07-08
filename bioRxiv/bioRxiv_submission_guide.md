# BioRxiv Submission Guide — BioResearch Agent

Step-by-step for posting the preprint. bioRxiv is the right first venue: it is life-sciences
focused (your content is literature + omics + MR), **free**, **no endorsement required**, and
assigns a **DOI** on posting.

---

## 0. What's in this folder

```
bioRxiv/
├── manuscript.pdf            ← upload this to bioRxiv
├── submission_metadata.md    ← copy-paste fields for the web form
├── cover_letter.md           ← optional; not required by bioRxiv
├── bioRxiv_submission_guide.md ← this file
└── source/                   ← LaTeX source (for recompiling / archival)
```

---

## 1. Create / sign in to bioRxiv

- Go to https://www.biorxiv.org
- Sign in, or create an account. You can authenticate via **ORCID** (recommended — your ORCID
  `0009-0002-5180-6226` will auto-link).

---

## 2. Start a new preprint

- Click **"Start a preprint"** (or "Submit a preprint").
- bioRxiv uses a single-upload flow; you do **not** need a separate source package.

---

## 3. Upload the manuscript

- Upload `manuscript.pdf`.
- bioRxiv accepts PDF directly. No LaTeX source upload needed (kept in `source/` for archival only).

---

## 4. Fill the web-form fields

Copy from `submission_metadata.md`:

| Field | Value |
|---|---|
| Title | BioResearch Agent: A Tool-First Framework for Structured Biomedical Research Workflows |
| Authors | Alimujiang Tudiyusufu (ORCID 0009-0002-5180-6226) |
| Abstract | (paste verbatim from metadata) |
| Keywords | Biomedical analysis, workflow framework, reproducibility, standardized interface, literature review, biomarker discovery, Mendelian randomization, bioinformatics |
| Subject area (primary) | **Bioinformatics** |
| Subject area (secondary) | **Genetics**, **Genomics** |
| Preprint category | **Tools and Resources** |
| License | **CC-BY** (default) |
| Code availability | https://github.com/Alim430/bioresearch-agent |

---

## 5. Author contributions / competing interests / funding

bioRxiv asks for these (they appear on the preprint page):

- **Author contributions:** A.T. conceived the framework, implemented the workflow engine and
  interfaces, validated outputs, and wrote the manuscript.
- **Competing interests:** The author declares no competing interests.
- **Funding:** No specific funding was received for this work.

---

## 6. Confirm and submit

- Confirm the work is not under consideration at a journal that prohibits preprint posting
  (most life-sciences journals allow bioRxiv; check if in doubt).
- Click **Submit**.
- bioRxiv runs scope + completeness screening (no peer review, no endorsement).
- **Posting typically completes in < 48 h**, after which a **DOI** is issued and the preprint is
  publicly indexed.

---

## 7. After posting

- You will get a DOI like `https://doi.org/10.1101/2026.xxxxxx`. Record it.
- bioRxiv permits **cross-posting to arXiv** later (and most journals permit bioRxiv preprints).
- You can post **revisions** (new PDF versions) anytime.

---

## Title consistency (important)

The uploaded `manuscript.pdf` title reads:
*"BioResearch Agent: A Tool-First Framework for Structured Biomedical Research Workflows"*

This matches the web-form title above, so the preprint is internally consistent.

If you instead want the title
*"BioResearch Agent: A Reproducible Workflow Framework for Biomedical Analysis Pipelines"*
(used in `../arxiv-abstract.md`), edit `source/main.tex`:

```latex
\title{BioResearch Agent: A Reproducible Workflow Framework for Biomedical Analysis Pipelines}
```

then recompile in an environment with a LaTeX toolchain:

```bash
cd bioRxiv/source
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
# replace manuscript.pdf with the newly compiled main.pdf
```

No LaTeX toolchain was available when this package was generated, so the existing PDF was used
as-is. **Do not change only the web-form title while leaving the PDF unchanged** — they must match.

---

## Why bioRxiv and not arXiv (right now)

- arXiv **requires endorsement** for this account on every archive (q-bio, cs) — confirmed
  empirically. bioRxiv requires none.
- Your content is life-sciences; bioRxiv reaches the exact audience (bioinformaticians,
  computational biologists) more directly than arXiv's q-bio.
- A bioRxiv DOI is a citable, permanent artifact you can later cross-post or cite from JOSS.
