# BioResearch Agent Framework — Architecture Reference

> **Version:** 3.0  
> **Scope:** Definitive architectural reference for the three-layer BioResearch Agent Framework  
> **Audience:** Framework developers, agent builders, researcher end-users  
> **Design Philosophy:** Evidence-centric, engine-first, human-in-the-loop

---

## Overview: The Three-Layer Architecture

The BioResearch Agent Framework is organized into three conceptual layers, each addressing a distinct question:

| Layer | Question | Count | Role |
|---|---|---|---|
| **Layer 1** | WHAT — What stage of research are we in? | 12 Stages | User-facing. Researchers understand this immediately. |
| **Layer 2** | HOW — How is this stage executed? | 6 Engines | Framework core. Reusable, domain-agnostic. |
| **Layer 3** | WHO — Which agent performs the work? | 23 Agents | Implementation details. Swappable, extensible. |

```
BioResearch Agent Framework
│
├── Layer 1: Research Lifecycle (WHAT — 12 Stages)
│   └── User-facing. Researchers understand this immediately.
│
├── Layer 2: Research Engines (HOW — 6 Core Engines)
│   └── Framework core. Reusable, domain-agnostic.
│
└── Layer 3: Specialized Agents (WHO — 23 Agents)
    └── Implementation details. Swappable, extensible.

Foundation: Shared Infrastructure
    ├── Evidence Store
    ├── Memory Layer
    ├── Knowledge Graph
    ├── State Manager
    └── Tool Plugin Manager
```

The Foundation provides cross-cutting services used by all three layers. Every data artifact, every decision, and every state transition flows through the Shared Infrastructure.

---

## Section 1: Layer 1 — Research Lifecycle (12 Stages)

Each stage is a user-visible milestone in the research process. A stage receives input from the previous stage, delegates execution to one or more Engines, produces output, and must pass a **Gate Condition** before the lifecycle can advance.

| Stage | Name | Powered By | Gate Condition |
|---|---|---|---|
| 1 | Ideation & Problem Identification | Question Engine | Research question is scoped, novel, and feasible |
| 2 | Hypothesis Generation | Question Engine | Hypothesis is falsifiable with ≥1 alternative |
| 3 | Literature Survey | Retrieval Engine | Coverage threshold met; gaps identified |
| 4 | Experimental Design | Retrieval Engine | Design passes statistical & ethical validation |
| 5 | Data Acquisition | Retrieval Engine | Data passes QC; provenance documented |
| 6 | Statistical Analysis | Analysis Engine | Analysis passes method audit; no critical flaws |
| 7 | Bioinformatics Analysis | Analysis Engine | Biological signals are reproducible |
| 8 | Causal Inference | Analysis Engine | Causal claims pass sensitivity & instrument checks |
| 9 | Evidence Integration & Grading | Evidence Engine | Aggregate confidence ≥ threshold; no unresolved critical conflicts |
| 10 | Narrative Construction | Narrative Engine | Manuscript is structurally complete with figures/tables |
| 11 | Pre-submission Review | Execution Engine | All major concerns resolved; accept probability ≥ threshold |
| 12 | Publication & Archiving | Execution Engine | All materials deposited; formats compliant |

### Stage 1: Ideation & Problem Identification

**Description:**  
Transforms a vague research interest into a scoped, evaluable scientific question. Assesses novelty, testability, publishability, and data availability.

**Powered By:** Question Engine  
**Input:** User query, research interest, domain context  
**Output:** Scored research question (novelty score, feasibility score, data availability flag), recommendation matrix (proceed / revise / pivot / abandon)  
**Gate Condition:** Novelty score ≥ threshold AND feasibility = "achievable" AND data availability = "sufficient"

### Stage 2: Hypothesis Generation

**Description:**  
Generates a falsifiable scientific hypothesis package: primary hypothesis, alternative hypotheses, null hypothesis, and explicit falsifiability criteria.

**Powered By:** Question Engine  
**Input:** Validated research question, domain context, preliminary literature signals  
**Output:** Hypothesis package (primary + alternatives + null + falsifiability design)  
**Gate Condition:** Hypothesis is falsifiable; ≥1 alternative hypothesis defined; testable with available or acquirable data

### Stage 3: Literature Survey

**Description:**  
Systematically retrieves, summarizes, and integrates relevant literature. Identifies knowledge gaps, tracks citation networks, and builds a working knowledge graph.

**Powered By:** Retrieval Engine  
**Input:** Hypothesis package, retrieval strategy parameters  
**Output:** Curated literature collection, knowledge graph fragment, gap list, trend analysis  
**Gate Condition:** Coverage ratio ≥ threshold (e.g., top-cited 80% of domain captured); ≥1 gap identified as addressable

### Stage 4: Experimental Design

**Description:**  
Designs a rigorous study protocol: study type selection, power analysis, control design, method selection, quality control plan, and ethics compliance checklist.

**Powered By:** Retrieval Engine  
**Input:** Hypothesis package, domain standards, literature-derived benchmarks  
**Output:** Protocol document, power analysis report, control matrix, QC checklist  
**Gate Condition:** Power ≥ 80% (or justified); controls defined; ethics checklist complete; no design-flaw flags

### Stage 5: Data Acquisition

**Description:**  
Acquires raw data from public databases or user-provided sources. Performs preprocessing, quality control, metadata extraction, and provenance logging.

**Powered By:** Retrieval Engine  
**Input:** Experimental protocol, database selection, access credentials  
**Output:** Preprocessed dataset, QC report, metadata bundle, provenance log  
**Gate Condition:** QC flags = 0 critical; missingness < threshold; batch effects documented (if any)

### Stage 6: Statistical Analysis

**Description:**  
Applies inferential statistics: descriptive statistics, hypothesis testing, multiple testing correction, effect size estimation, confidence intervals, and methodological audit.

**Powered By:** Analysis Engine  
**Input:** Preprocessed dataset, hypothesis package, design parameters  
**Output:** Statistical results table, effect sizes, p-values / FDR, confidence intervals, method audit report  
**Gate Condition:** Method audit passes; no critical statistical flaws; assumptions verified

### Stage 7: Bioinformatics Analysis

**Description:**  
Executes domain-specific computational biology: differential expression, pathway enrichment, multi-omics integration, network analysis, single-cell analysis.

**Powered By:** Analysis Engine  
**Input:** Preprocessed dataset, domain annotations, reference databases  
**Output:** Differential feature lists, enrichment results, network structures, single-cell embeddings  
**Gate Condition:** Biological signals reproducible across subsamples; no batch-driven artifacts; pathways interpretable

### Stage 8: Causal Inference

**Description:**  
Elevates association to causation: Mendelian randomization, colocalization, causal graph construction, instrument variable validation, bidirectional testing.

**Powered By:** Analysis Engine  
**Input:** Statistical results, genotype data or GWAS summary statistics, causal assumptions  
**Output:** Causal effect estimates, sensitivity analyses, colocalization posteriors, causal DAG  
**Gate Condition:** Instruments pass strength threshold (F > 10); no unresolvable pleiotropy; sensitivity analyses robust

### Stage 9: Evidence Integration & Grading

**Description:**  
Consolidates all evidence produced across Stages 3–8. Applies A–E grading, detects conflicts, computes aggregate confidence, identifies evidence gaps.

**Powered By:** Evidence Engine  
**Input:** All evidence artifacts from preceding stages, hypothesis package  
**Output:** Integrated evidence report, A–E grading table, conflict inventory, aggregate confidence score, evidence graph  
**Gate Condition:** Aggregate confidence ≥ "moderate"; no unresolved critical conflicts; evidence sufficiency flag = true

### Stage 10: Narrative Construction

**Description:**  
Transforms evidence into a structured scientific manuscript: IMRAD architecture, storyline, figures, tables, methodology descriptions, and discussion framework.

**Powered By:** Narrative Engine  
**Input:** Integrated evidence report, manuscript type (original research / review / methodology), target journal guidelines  
**Output:** Complete manuscript draft, figure set, table set, methods description, discussion skeleton  
**Gate Condition:** All required sections present; figures and tables cross-referenced; word count within journal limits

### Stage 11: Pre-submission Review

**Description:**  
Simulates the peer-review process from multiple perspectives—statistical, domain, translational—before actual submission. Generates a revision plan.

**Powered By:** Execution Engine  
**Input:** Manuscript draft, evidence graph, target journal profile  
**Output:** Multi-perspective review report (major / minor concerns), revision plan, estimated accept probability  
**Gate Condition:** All major concerns have remediation plans; accept probability ≥ journal-specific threshold

### Stage 12: Publication & Archiving

**Description:**  
Finalizes the submission package: journal recommendation, format compliance, cover letter generation, data/code deposition, version control, and post-publication dissemination plan.

**Powered By:** Execution Engine  
**Input:** Finalized manuscript, data package, code repository, author instructions  
**Output:** Submission materials, archived datasets, version records, dissemination assets  
**Gate Condition:** All required files deposited; formatting passes journal validation checklist; ORCID / affiliation metadata complete

---

## Section 2: Layer 2 — Research Engines (6 Core Engines)

Engines are the **framework's core contribution**. They are domain-agnostic, reusable orchestration units. Each Engine exposes a standard interface and manages a cohort of Specialized Agents (Layer 3).

### Standard Engine Interface

Every Engine implements the following contract:

```python
class ResearchEngine(ABC):
    @abstractmethod
    def validate(self, state: ResearchState) -> ValidationResult:
        """Validate that the current state contains all required inputs for this engine."""
        pass

    @abstractmethod
    def run(self, state: ResearchState) -> ResearchState:
        """Execute the engine's core logic, updating the state with new artifacts."""
        pass

    @abstractmethod
    def gate(self, state: ResearchState) -> GateResult:
        """Evaluate gate conditions. Returns PASS, CONDITIONAL, or FAIL with reasoning."""
        pass
```

**Why this design?**
- **Reusability:** The same Engine powers multiple stages and multiple workflow templates.
- **Testability:** `validate()`, `run()`, and `gate()` can be unit-tested independently.
- **Observability:** Gate results provide explicit, auditable decision points.
- **Swappability:** An Engine can be replaced or upgraded without changing stage definitions.

---

### Engine 1: Question Engine

| Attribute | Detail |
|---|---|
| **Responsibility** | Transform raw curiosity into rigorous, falsifiable research questions and hypotheses |
| **Lifecycle Stages** | Stage 1 (Ideation), Stage 2 (Hypothesis Generation) |
| **Sub-agents Managed** | IdeaAgent, NoveltyAgent, BrainstormAgent, HypothesisAgent |
| **Interface** | `validate()` → `run()` → `gate()` |

**Why it's designed this way:**  
The Question Engine sits at the top of the funnel. If the question is ill-posed, nothing downstream can rescue it. By isolating ideation into its own Engine—rather than scattering it across ad-hoc agents—the framework enforces a hard boundary: no hypothesis proceeds to Retrieval without passing novelty and falsifiability gates.

---

### Engine 2: Retrieval Engine

| Attribute | Detail |
|---|---|
| **Responsibility** | Acquire external knowledge and raw data: literature, databases, protocols, metadata |
| **Lifecycle Stages** | Stage 3 (Literature Survey), Stage 4 (Experimental Design), Stage 5 (Data Acquisition) |
| **Sub-agents Managed** | LiteratureAgent, KnowledgeGraphAgent, DesignAgent, DataCollectionAgent |
| **Interface** | `validate()` → `run()` → `gate()` |

**Why it's designed this way:**  
Retrieval is a cross-cutting concern that spans literature, experimental planning, and data download. Unifying these under one Engine prevents duplicated search logic, ensures consistent metadata handling, and allows a single provenance log to track every external resource the framework touches.

---

### Engine 3: Analysis Engine

| Attribute | Detail |
|---|---|
| **Responsibility** | Execute all computational and statistical analyses: statistics, bioinformatics, causal inference |
| **Lifecycle Stages** | Stage 6 (Statistical Analysis), Stage 7 (Bioinformatics Analysis), Stage 8 (Causal Inference) |
| **Sub-agents Managed** | StatisticalAgent, BioinformaticsAgent, MultiOmicsAgent, CausalInferenceAgent, PathwayAgent, NetworkAgent |
| **Interface** | `validate()` → `run()` → `gate()` |

**Why it's designed this way:**  
Analysis stages share common needs: input validation, assumption checking, reproducibility logging, and sensitivity testing. Co-locating statistical, bioinformatic, and causal agents under one Engine enables shared analytical infrastructure (e.g., a unified results schema, common sensitivity-analysis runners) without forcing each agent to reimplement it.

---

### Engine 4: Evidence Engine

| Attribute | Detail |
|---|---|
| **Responsibility** | Grade, integrate, and track confidence of all evidence produced across the lifecycle |
| **Lifecycle Stage** | Stage 9 (Evidence Integration & Grading) |
| **Sub-agents Managed** | EvidenceGradingAgent, ConflictDetectionAgent, ConfidenceAgent |
| **Interface** | `validate()` → `run()` → `gate()` |

**Why it's designed this way:**  
Evidence is the framework's central currency. The Evidence Engine is deliberately narrow and deep: it does not generate new evidence, it *adjudicates* evidence. This separation of concerns prevents analysis agents from grading their own homework and ensures that confidence calculations are performed by a dedicated, impartial subsystem.

---

### Engine 5: Narrative Engine

| Attribute | Detail |
|---|---|
| **Responsibility** | Transform structured evidence into human-readable scientific narrative: manuscripts, figures, tables |
| **Lifecycle Stage** | Stage 10 (Narrative Construction) |
| **Sub-agents Managed** | SynthesisAgent, WritingAgent, FigureAgent |
| **Interface** | `validate()` → `run()` → `gate()` |

**Why it's designed this way:**  
Narrative construction is a generative art that requires coherent context from every upstream stage. The Narrative Engine acts as the "compiler" of the research process: it takes the evidence graph, results tables, and causal DAG as inputs, and outputs a unified manuscript. Isolating narrative generation prevents analysis agents from leaking presentation bias into results.

---

### Engine 6: Execution Engine

| Attribute | Detail |
|---|---|
| **Responsibility** | Execute the final quality assurance and delivery pipeline: review simulation, journal matching, formatting, archiving |
| **Lifecycle Stages** | Stage 11 (Pre-submission Review), Stage 12 (Publication & Archiving) |
| **Sub-agents Managed** | ReviewerAgent, JournalAgent, ArchivingAgent |
| **Interface** | `validate()` → `run()` → `gate()` |

**Why it's designed this way:**  
The Execution Engine handles "last-mile" operations that are procedural rather than intellectual. By grouping review simulation and publication logistics together, the framework ensures that the same quality bar applied at Stage 11 (review) is enforced through Stage 12 (archiving). It also provides a clean separation between *what* the science says (Narrative Engine) and *how* it is delivered (Execution Engine).

---

## Section 3: Layer 3 — Specialized Agents (23 Agents)

Layer 3 is where concrete implementation lives. Agents are **swappable**: a domain-specific agent can replace a generic one without altering the Engine contract or the stage definition.

### Question Engine → 4 Agents
1. **IdeaAgent** — Generates and refines raw research ideas from user prompts
2. **NoveltyAgent** — Computes novelty scores by comparing against existing literature
3. **BrainstormAgent** — Produces cross-domain method transfer suggestions
4. **HypothesisAgent** — Packages primary, alternative, and null hypotheses with falsifiability criteria

### Retrieval Engine → 4 Agents
5. **LiteratureAgent** — Executes systematic searches across PubMed, arXiv, bioRxiv, Semantic Scholar, OpenAlex
6. **KnowledgeGraphAgent** — Builds entity-relationship-evidence networks from retrieved literature
7. **DesignAgent** — Generates study protocols, power analyses, and control matrices
8. **DataCollectionAgent** — Downloads and preprocesses data from GEO, TCGA, SRA, UK Biobank, CellxGene, dbGaP, FinnGen

### Analysis Engine → 6 Agents
9. **StatisticalAgent** — Performs descriptive and inferential statistics, multiple testing correction, effect size estimation
10. **BioinformaticsAgent** — Runs differential expression, enrichment, and functional annotation pipelines
11. **MultiOmicsAgent** — Integrates transcriptomic, proteomic, metabolomic, and epigenomic datasets
12. **CausalInferenceAgent** — Executes Mendelian randomization, colocalization, and causal graph inference
13. **PathwayAgent** — Specializes in pathway enrichment (GSEA, KEGG, GO, Reactome, Hallmark)
14. **NetworkAgent** — Constructs and analyzes PPI, WGCNA, and gene co-expression networks

### Evidence Engine → 3 Agents
15. **EvidenceGradingAgent** — Assigns A–E grades to individual evidence items
16. **ConflictDetectionAgent** — Identifies logical or empirical conflicts across evidence sources
17. **ConfidenceAgent** — Computes aggregate confidence scores weighted by evidence grade and independence

### Narrative Engine → 3 Agents
18. **SynthesisAgent** — Designs the manuscript structure (IMRAD, structured abstract) and storyline
19. **WritingAgent** — Drafts paragraphs for methods, results, and discussion sections
20. **FigureAgent** — Generates figures, tables, and visual summaries from analysis outputs

### Execution Engine → 3 Agents
21. **ReviewerAgent** — Simulates statistical, domain, and translational peer-review perspectives
22. **JournalAgent** — Matches manuscripts to journals by scope, impact, and acceptance rate; formats to journal guidelines
23. **ArchivingAgent** — Deposits data, code, and supplementary materials; manages versioning and preprint submission

---

## Section 4: Shared Infrastructure

The Foundation is a set of cross-cutting services used by all Engines and Agents. No layer operates without it.

### Evidence Store

Central repository for all evidence artifacts produced during a research project.

- **A–E Grading Schema:**
  - **A** — Direct experimental validation (gold standard)
  - **B** — Multiple independent sources consistent (strong)
  - **C** — Indirect association or surrogate endpoint (moderate)
  - **D** — Conflicting or contradictory evidence (weak / contested)
  - **E** — Speculation, extrapolation, or expert opinion only (unverified)
- **Conflict Tracking:** Every evidence item is tagged with its supporting and opposing relationships. Conflicts are surfaced automatically when two A- or B-grade items contradict.
- **Provenance:** Full traceability from raw data → analysis → grading → narrative claim.

### Memory Layer

Persistent, searchable memory across time scales.

- **Project Memory:** All decisions, parameter choices, abandoned branches, and intermediate results for the current project.
- **Failure Log:** A structured record of falsified hypotheses, rejected analyses, and gate failures. Prevents the framework from repeating failed paths.
- **Cross-Project Memory:** (Optional) Domain-level accumulation of insights across multiple projects, respecting data isolation boundaries.

### Knowledge Graph

A dynamic, queryable graph representing the research domain.

- **Nodes:** Entities (genes, proteins, diseases, compounds, methods, hypotheses)
- **Edges:** Relationships (regulates, associates_with, contradicts, supports, precedes)
- **Evidence Linkage:** Every edge is annotated with the evidence items (from the Evidence Store) that justify it.
- **Temporal Tracking:** The graph evolves as new literature is retrieved and new analyses are completed.

### State Manager

Ensures persistence and recoverability of the research process.

- **ResearchState Object:** A serializable, versioned container holding the complete state of an in-flight research project.
- **Checkpointing:** Automatic save at every Gate. Projects can be resumed from any Gate.
- **Branching:** Supports exploratory branches (e.g., "What if we test Hypothesis B instead?") without destroying the main timeline.
- **Audit Trail:** Immutable log of every state transition, agent invocation, and user approval.

### Tool Plugin Manager

Unified interface to external tools, databases, and APIs.

| Category | Examples |
|---|---|
| Literature | PubMed, arXiv, bioRxiv, medRxiv, Semantic Scholar, OpenAlex |
| Databases | GEO, TCGA, SRA, UK Biobank, CellxGene, dbGaP, FinnGen, ADNI |
| Bioinformatics | scanpy, Seurat, clusterProfiler, DESeq2, limma, edgeR |
| Causality | TwoSampleMR, coloc, MR-PRESSO, MendelianRandomization |
| Visualization | matplotlib, seaborn, ggplot2, Cytoscape |
| Productivity | Zotero, Notion, GitHub, Overleaf |
| LLM Providers | OpenAI, Anthropic, Local LLMs, Embedding Models |

- **Mock Mode:** Every plugin implements a mock interface for offline testing and reproducible demos.
- **Live Mode:** Production execution calls real APIs with rate-limiting, retry logic, and credential management.
- **Registration:** New tools are registered via a declarative manifest; no Engine or Agent code needs modification.

---

## Section 5: Six Workflow Templates

Workflow templates define which stages are included for a given research goal. Not every project requires all 12 stages.

| Workflow | Purpose | Stage Sequence |
|---|---|---|
| **Discovery** | Biomarker or target discovery from omics data | 1 → 2 → 3 → 5 → 6 → 7 → 9 → 10 → 11 → 12 |
| **Mechanism** | Elucidating causal biological mechanisms | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 |
| **Clinical** | Translational or clinical validation studies | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 |
| **Methodology** | Computational or experimental method development | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 9 → 10 → 11 → 12 |
| **Review** | Systematic or narrative literature review | 1 → 2 → 3 → 10 → 11 → 12 |
| **Grant** | Research proposal or fellowship application | 1 → 2 → 3 → 4 → 10 → 11 → 12 |

**Template Selection Logic:**  
The Orchestrator selects the default template based on the user's initial query. The user may override at any time. Template selection pre-configures stage gates (e.g., a Grant workflow may relax the Evidence Engine gate because funding proposals typically contain preliminary rather than definitive evidence).

---

## Section 6: Data Flow

### Forward Flow: The Happy Path

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│ Stage 1: Ideation                   │ ← Question Engine validates & runs
│ Gate 1: Novelty + Feasibility       │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 2: Hypothesis                 │ ← Question Engine validates & runs
│ Gate 2: Falsifiability              │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 3: Literature Survey          │ ← Retrieval Engine validates & runs
│ Gate 3: Coverage Threshold          │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 4: Experimental Design        │ ← Retrieval Engine validates & runs
│ Gate 4: Power + Ethics              │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 5: Data Acquisition           │ ← Retrieval Engine validates & runs
│ Gate 5: QC + Provenance             │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stages 6–8: Analysis                │ ← Analysis Engine validates & runs
│ Gate 6: Method Audit                │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 9: Evidence Integration       │ ← Evidence Engine validates & runs
│ Gate 7: Confidence Threshold        │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 10: Narrative                 │ ← Narrative Engine validates & runs
│ Gate 8: Structural Completeness     │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 11: Pre-submission Review     │ ← Execution Engine validates & runs
│ Gate 9: Accept Probability          │
└─────────────────────────────────────┘
    │ PASS
    ▼
┌─────────────────────────────────────┐
│ Stage 12: Publication & Archiving   │ ← Execution Engine validates & runs
│ Gate 10: Compliance                 │
└─────────────────────────────────────┘
    │
    ▼
Output: Manuscript + Data + Archive
```

### Gate Checks & State Transitions

At every Gate, the framework evaluates three dimensions:

1. **Automated Check:** The Engine's `gate()` method evaluates quantitative thresholds.
2. **Conflict Scan:** The Evidence Store checks for newly introduced critical conflicts.
3. **Human Decision:** The user receives a summary and may **Approve**, **Request Revision**, or **Abandon**.

**State transitions:**
- `APPROVE` → Advance to next stage
- `REVISION` → Loop within current stage (Engine re-runs with modified parameters)
- `ABANDON` → Archive project state; return to Stage 1 or terminate

### Backward Iteration Paths

Research is rarely linear. The framework supports structured backtracking:

| Trigger | Backtrack To | Rationale |
|---|---|---|
| Gate 9 (Review) finds fatal statistical flaw | Stage 6–8 (Analysis) | Re-analysis with corrected methods |
| Gate 7 (Evidence) finds insufficient evidence | Stage 3 (Literature) or Stage 5 (Data) | Supplement literature or acquire new data |
| Gate 6 (Analysis) finds batch effect | Stage 5 (Data Acquisition) | Re-download or re-process with corrected QC |
| Gate 4 (Design) finds underpowered design | Stage 2 (Hypothesis) | Relax hypothesis or change study type |
| Gate 2 (Hypothesis) finds non-falsifiable question | Stage 1 (Ideation) | Re-scope the research question |

All backtracking is logged in the State Manager's audit trail. When backtracking occurs, downstream artifacts are marked `STALE` and regenerated on the next forward pass.

---

## Section 7: Design Principles

### 1. Evidence-Centric (A–E Grading)

Every claim in the framework must be traceable to graded evidence. Agents do not "believe"—they report confidence levels. The A–E grading system forces explicit epistemic humility:

- An agent cannot upgrade C-grade evidence to A-grade without new data.
- Conflicting A-grade evidence triggers an automatic escalation to the user.
- The Narrative Engine cannot state a claim in the Results section unless the Evidence Engine has assigned it ≥ B-grade.

### 2. Human-in-the-Loop (Gates)

No stage advances without an explicit Gate. Gates are not bureaucratic checkpoints; they are **decision surfaces** where human judgment is injected. The framework defaults to conservative behavior: if confidence is borderline, it asks rather than assumes.

### 3. Engine-First (Contribution Is Engines, Not Agents)

The framework's reusable value lies in its six Engines, not in any individual agent. An agent is a replaceable worker; an Engine is a contractual boundary. When extending the framework:

- **Add an agent** when a new analysis method emerges (e.g., a new deep-learning variant caller).
- **Add an engine** only when a fundamentally new research phase is identified that none of the existing six can cover.

### 4. Mock-to-Live (All Tools Have Mock + Live Modes)

Every plugin in the Tool Plugin Manager implements both modes:

- **Mock Mode:** Returns deterministic, cached responses. Used for development, testing, demos, and reproducibility verification. No API keys required. No rate limits.
- **Live Mode:** Calls real external APIs. Used for production research. Subject to rate limits, costs, and data freshness.

The transition from mock to live is a single configuration switch. This ensures that a workflow tested end-to-end in mock mode will execute identically (modulo data values) in live mode.

---

## Appendix: Mapping Quick Reference

| If you want to... | Use Stage... | Powered By Engine... | Managed By Agents... |
|---|---|---|---|
| Evaluate a research idea | Stage 1 | Question Engine | IdeaAgent, NoveltyAgent |
| Generate a falsifiable hypothesis | Stage 2 | Question Engine | HypothesisAgent, BrainstormAgent |
| Survey literature and build a knowledge graph | Stage 3 | Retrieval Engine | LiteratureAgent, KnowledgeGraphAgent |
| Design a study with power analysis | Stage 4 | Retrieval Engine | DesignAgent |
| Download and preprocess public data | Stage 5 | Retrieval Engine | DataCollectionAgent |
| Run statistical tests and correct for multiple comparisons | Stage 6 | Analysis Engine | StatisticalAgent |
| Perform differential expression / pathway enrichment | Stage 7 | Analysis Engine | BioinformaticsAgent, PathwayAgent, NetworkAgent |
| Run Mendelian randomization or colocalization | Stage 8 | Analysis Engine | CausalInferenceAgent |
| Grade evidence and detect conflicts | Stage 9 | Evidence Engine | EvidenceGradingAgent, ConflictDetectionAgent, ConfidenceAgent |
| Write a manuscript with figures and tables | Stage 10 | Narrative Engine | SynthesisAgent, WritingAgent, FigureAgent |
| Simulate peer review before submission | Stage 11 | Execution Engine | ReviewerAgent |
| Submit to a journal and archive data | Stage 12 | Execution Engine | JournalAgent, ArchivingAgent |

---

*BioResearch Agent Framework v3.0 | Three-Layer Architecture | Evidence-Centric | Engine-First | Human-in-the-Loop*
