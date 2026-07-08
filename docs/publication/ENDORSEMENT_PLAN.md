# arXiv Endorsement Plan — BioResearch Agent Framework

> Strategy (2026-07-08): **Try endorsement once, but do not block progress on it.** Keep the
> project positioning unchanged. If no endorser is found, fall back to JOSS (no endorsement
> needed), then arXiv later.

## 1. Account reality (verified)

This arXiv account (foxmail + `almj@ibms.pumc.edu.cn`) is **not auto-endorsed for any archive**.
Both personal and institutional emails failed auto-recognition, so **every archive requires a
human endorser**. There is no "pick a category that skips endorsement" shortcut.

## 2. Recommended arXiv category

| Priority | Archive | Why |
|:---|:---|:---|
| **1 (primary target)** | **cs.SE** — Software Engineering | Best match for "reproducible software framework / workflow execution / standardized interfaces / API". Lowest risk of a "where is the AI contribution?" rejection. |
| 2 (secondary) | **q-bio.QM** / **q-bio.GN** | Use if emphasizing the biomedical side (omics / biomarker / MR). One q-bio endorsement covers both subclasses. |
| **Avoid** | **cs.AI** | Weak AI contribution → reviewers ask "where is the AI?" and may class it as mere application, not AI research. Only add cs.AI as a secondary if an endorser suggests it. |

**Do NOT change the paper title or positioning to chase endorsement.** Keep
"BioResearch Agent Framework: A Reproducible Workflow Framework for Biomedical Analysis".

## 3. How to frame the request (high-success wording)

❌ Weak: *"Can you endorse my AI paper?"*
✅ Strong: *"I developed an open-source biomedical workflow framework and would like to submit it
to arXiv cs.SE / q-bio. Would you be willing to endorse my submission?"*

Emphasize: reproducible software infrastructure + standardized interfaces; explicitly state it is
**not** a new algorithm. This matches what cs.SE / q-bio endorsers expect to vouch for.

## 4. Who to ask (prioritized)

### Tier A — your own network (highest probability)
- Colleagues / PIs at **Shanghai University of Traditional Chinese Medicine** and **PUMC IBMS**
  who have posted to arXiv in the last 5 years.
- How to find them: search your institution's publication list; or on arXiv use
  `searchtype=author` with known faculty names; or check if co-authors on your prior work have
  arXiv records.
- A single q-bio endorsement (from anyone in Tier A who has a q-bio paper) covers q-bio.QM+GN.

### Tier B — bioinformatics workflow / software PIs (precise, ≤5 emails)
Concrete adjacent community (workflow reproducibility, bioinformatics tooling):
- **Sarah Cohen-Boulakia**, **Ulf Leser**, **Aurélie Névéol** et al. — authors of
  *"Supporting Workflow Reproducibility by Linking Bioinformatics Tools across Papers and
  Executable Code"* (arXiv:2603.08195, 2026). Their work is directly adjacent to this project.
  Note: that paper is filed under **cs.CL**, so treat them as **q-bio / cs.DB** endorser
  candidates, not cs.SE. Find their current contact via the arXiv author page or lab website.
- More leads: authors of Nextflow / Snakemake / Galaxy / TwoSampleMR / limma software papers who
  have arXiv records. Search `arxiv.org` for those tool names + "workflow" / "reproducibility".

### Tier C — do NOT do
- Mass / bulk endorsement requests. arXiv explicitly discourages this; 5 precise emails beat
  100 spam.

## 5. Ready-to-send email template

```
Subject: arXiv endorsement request — cs.SE / q-bio (biomedical workflow framework)

Dear [Name],

I'm [Your Name], a researcher at [Shanghai University of Traditional Chinese Medicine / PUMC IBMS].
I've built an open-source, reproducible workflow framework for biomedical analysis (literature
review, biomarker discovery, Mendelian randomization) and would like to post it as a preprint to
the arXiv cs.SE (Software Engineering) archive — or q-bio if you prefer.

Title: "BioResearch Agent Framework: A Reproducible Workflow Framework for Biomedical Analysis"

The contribution is a reproducible execution contract that integrates existing biomedical tools
(limma-style DEG, hypergeometric enrichment, TwoSampleMR-style IVW) behind standardized
CLI / SDK / API and Agent-Skills interfaces — not a new algorithm. Code:
https://github.com/Alim430/bioresearch-agent

I'm not yet endorsed for the cs.SE / q-bio archive and would be grateful for your endorsement.
arXiv should have sent a request to this address; confirming the link is all that's needed.

Thank you,
[Your Name]
almj@ibms.pumc.edu.cn
```

## 6. Fallback if no endorser (do not stop)

```
GitHub v1.1 (skills expansion done)
   → Zenodo DOI (archive a tagged release)
   → JOSS submission (peer-reviewed software paper, no endorsement needed)
   → later: arXiv cs.SE (after JOSS acceptance you have a citable record; endorsement easier)
```

bioRxiv is a secondary option only if a **real biological finding** is added (e.g., a Parkinson's
disease biomarker case study on GSE7621) — see the case-study gap below.

## 7. Biggest paper weakness (track this)

Current validation is thin: literature (synthetic fallback), biomarker (GSE7621 example),
causal (simulated GWAS). For a *software* paper this is acceptable, but impact is weak. A
**case study** that recovers known PD genes (SNCA, LRRK2, …) from GSE7621 would materially
strengthen the paper and is the priority for a future v2.0.
