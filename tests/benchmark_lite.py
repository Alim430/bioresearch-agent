"""Benchmark-Lite: 21-task regression suite for BioResearch Agent v1.6.

Runs without pytest, without network, without external data. Every task is a
self-contained assertion that a core framework contract still holds after
code changes. Designed to be run as:

    python tests/benchmark_lite.py          # standalone
    pytest tests/benchmark_lite.py -v       # pytest-compatible

The 21 tasks are grouped into seven domains:

    A. Router (8)       — intent classification & command mapping
    B. Core State (3)   — Stage, EvidenceGrade, ResearchState
    C. Engines (6)      — each of the 6 Layer-2 engines in isolation
    D. Pipeline (1)     — full 6-engine chain, IDEATION -> PUBLICATION
    E. Registry (1)     — skills/registry.json structural integrity
    F. Manifest+Gov (1) — eval/manifest.json + .gitignore governance
    G. Foundation (1)   — foundation-embeddings mock pipeline validation
"""
from __future__ import annotations

import json
import os
import sys
import random
from pathlib import Path

# -- path setup ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bio-research-os"))

# -- imports ------------------------------------------------------------------
from bioresearch.router import (  # noqa: E402
    classify_intent,
    route_to_command,
    AVAILABLE_ROUTES,
    ROUTE_KEYWORDS,
    ROUTE_PRIORITY,
)
from core.state import (  # noqa: E402
    Stage,
    EvidenceGrade,
    ResearchState,
    Hypothesis,
    Evidence,
    GateResult,
)
from engines.question_engine import QuestionEngine  # noqa: E402
from engines.retrieval_engine import RetrievalEngine  # noqa: E402
from engines.analysis_engine import AnalysisEngine  # noqa: E402
from engines.evidence_engine import EvidenceEngine  # noqa: E402
from engines.narrative_engine import NarrativeEngine  # noqa: E402
from engines.execution_engine import ExecutionEngine  # noqa: E402


# =============================================================================
#  Group A — Router (Tasks 1-8)
# =============================================================================

def task_01_biomarker_routing():
    """Biomarker intent (GEO + DEG keywords) routes to 'biomarker'."""
    r = classify_intent("find biomarkers for Parkinson's disease using GSE7621")
    assert r["route"] == "biomarker"
    assert r["confidence"] > 0
    assert len(r["matched_keywords"]) > 0


def task_02_causal_routing():
    """Causal/MR intent routes to 'causal' with MR keyword."""
    r = classify_intent("Mendelian randomization of BMI on type 2 diabetes")
    assert r["route"] == "causal"
    assert "mendelian randomization" in r["matched_keywords"]


def task_03_literature_routing():
    """Literature review intent routes to 'literature'."""
    r = classify_intent("do a literature review on microglia in Alzheimer's disease")
    assert r["route"] == "literature"
    assert r["confidence"] >= 0.5


def task_04_doctor_routing():
    """Environment check intent routes to 'doctor'."""
    r = classify_intent("validate the installation and check dependencies")
    assert r["route"] == "doctor"
    assert r["confidence"] > 0


def task_05_case_study_routing():
    """Case study / benchmark intent routes to 'case-study'."""
    r = classify_intent("run a disease case study validation on real data")
    assert r["route"] == "case-study"


def task_06_unknown_intent():
    """Unrecognised intent returns 'unknown' with suggestion list."""
    r = classify_intent("what is the meaning of life")
    assert r["route"] == "unknown"
    assert r["confidence"] == 0.0
    assert r["suggestion"] == AVAILABLE_ROUTES


def task_07_router_determinism():
    """Same input produces identical output (deterministic, no LLM)."""
    a = classify_intent("differential expression analysis of microarray data")
    b = classify_intent("differential expression analysis of microarray data")
    assert a == b


def task_08_route_to_command():
    """route_to_command maps every route to a non-empty CLI string."""
    for route in AVAILABLE_ROUTES:
        cmd = route_to_command(route)
        assert isinstance(cmd, str)
        assert len(cmd) > 0
    assert route_to_command("unknown") == "bioresearch --help"


# =============================================================================
#  Group B — Core State (Tasks 9-11)
# =============================================================================

def task_09_stage_enum():
    """Stage enum has exactly 12 stages, ordered 1-12."""
    stages = list(Stage)
    assert len(stages) == 12
    for i, s in enumerate(stages, 1):
        assert s.value == i
    assert Stage.IDEATION.value == 1
    assert Stage.PUBLICATION.value == 12


def task_10_evidence_grade_enum():
    """EvidenceGrade has 5 grades A through E."""
    grades = list(EvidenceGrade)
    assert len(grades) == 5
    assert [g.value for g in grades] == ["A", "B", "C", "D", "E"]
    assert EvidenceGrade.A.value == "A"
    assert EvidenceGrade.E.value == "E"


def task_11_research_state_init():
    """ResearchState initializes with correct defaults and serialises via to_dict."""
    state = ResearchState()
    assert state.current_stage == Stage.IDEATION
    assert state.run_id  # auto-generated UUID
    assert state.literature == []
    assert state.datasets == []
    assert state.statistical_results is None
    assert state.bioinformatics_results is None
    assert state.causal_estimates is None
    assert state.integrated_evidence is None
    assert state.manuscript is None

    d = state.to_dict()
    assert d["current_stage"] == "IDEATION"
    assert d["literature_count"] == 0
    assert d["dataset_count"] == 0


# =============================================================================
#  Group C — Engines (Tasks 12-17)
# =============================================================================

def task_12_question_engine():
    """QuestionEngine generates a hypothesis with falsifiability criteria."""
    random.seed(42)
    eng = QuestionEngine(mock_mode=True)
    state = ResearchState()
    state = eng.run(state, query="effect of inflammation on neurodegeneration")
    assert state.hypothesis is not None
    assert state.hypothesis.primary  # non-empty
    assert state.hypothesis.null_hypothesis  # non-empty
    assert len(state.hypothesis.falsifiability_criteria) >= 1
    assert 0.0 <= state.hypothesis.confidence <= 1.0
    assert state.current_stage == Stage.HYPOTHESIS_GENERATION

    gate = eng.gate(state)
    assert gate.can_proceed is True


def task_13_retrieval_engine():
    """RetrievalEngine produces >=5 papers, >=1 dataset, and a QC report."""
    random.seed(42)
    eng = RetrievalEngine(mock_mode=True)
    state = ResearchState()
    state.hypothesis = Hypothesis(primary="test hypothesis about inflammation")
    state = eng.run(state)
    assert len(state.literature) >= 5
    assert len(state.datasets) >= 1
    assert state.qc_report is not None
    assert "literature_count" in state.qc_report
    assert "dataset_count" in state.qc_report
    assert "qc_warnings" in state.qc_report
    assert state.current_stage == Stage.KNOWLEDGE_GRAPH_BUILDING


def task_14_analysis_engine():
    """AnalysisEngine produces statistical, bioinformatics, and causal results."""
    random.seed(42)
    eng = AnalysisEngine(mock_mode=True)
    state = ResearchState()
    state.hypothesis = Hypothesis(primary="test")
    state.datasets = [{"samples": 100, "features": 5000}]
    state = eng.run(state)
    assert state.statistical_results is not None
    assert "tests" in state.statistical_results
    assert state.bioinformatics_results is not None
    assert "differential_molecules" in state.bioinformatics_results
    assert "enrichment" in state.bioinformatics_results
    assert state.causal_estimates is not None
    assert "estimate_ate" in state.causal_estimates
    assert "method" in state.causal_estimates
    assert state.current_stage == Stage.CAUSAL_INFERENCE


def task_15_evidence_engine():
    """EvidenceEngine grades evidence and computes aggregate confidence."""
    random.seed(42)
    eng = EvidenceEngine(mock_mode=True)
    state = ResearchState()
    state.hypothesis = Hypothesis(primary="test")
    state.statistical_results = {"n_samples": 100}
    state.bioinformatics_results = {"differential_molecules": []}
    state.causal_estimates = {"estimate_ate": 0.5}
    state.literature = [{"title": "paper1"}, {"title": "paper2"}]
    state = eng.run(state)
    assert state.integrated_evidence is not None
    assert "grades" in state.integrated_evidence
    assert "conflict_report" in state.integrated_evidence
    assert "aggregate_confidence" in state.integrated_evidence
    conf = state.integrated_evidence["aggregate_confidence"]
    assert 0.0 <= conf <= 1.0
    assert state.current_stage == Stage.EVIDENCE_INTEGRATION


def task_16_narrative_engine():
    """NarrativeEngine produces manuscript with IMRAD sections and figures."""
    random.seed(42)
    eng = NarrativeEngine(mock_mode=True)
    state = ResearchState()
    state.integrated_evidence = {"sources": [], "grades": {}, "aggregate_confidence": 0.7}
    state.statistical_results = {"n_samples": 100}
    state.bioinformatics_results = {"differential_molecules": []}
    state.causal_estimates = {"estimate_ate": 0.5}
    state = eng.run(state)
    assert state.manuscript is not None
    assert "title" in state.manuscript
    assert "sections" in state.manuscript
    for sec in ["Introduction", "Methods", "Results", "Discussion"]:
        assert sec in state.manuscript["sections"]
    assert "Abstract" in state.manuscript["sections"]
    assert len(state.figures) >= 1
    assert len(state.tables) >= 1
    assert state.current_stage == Stage.NARRATIVE_CONSTRUCTION


def task_17_execution_engine():
    """ExecutionEngine produces review report and submission materials."""
    random.seed(42)
    eng = ExecutionEngine(mock_mode=True)
    state = ResearchState()
    state.manuscript = {"title": "Test Manuscript", "sections": {}}
    state = eng.run(state)
    assert state.review_report is not None
    assert "reviews" in state.review_report
    assert "consensus" in state.review_report
    assert state.submission_materials is not None
    assert "target_journal" in state.submission_materials
    assert "cover_letter" in state.submission_materials
    assert "file_manifest" in state.submission_materials
    assert 0.0 <= state.accept_probability <= 1.0
    assert state.current_stage == Stage.PUBLICATION


# =============================================================================
#  Group D — Pipeline (Task 18)
# =============================================================================

def task_18_full_pipeline():
    """Full 6-engine chain: IDEATION -> PUBLICATION, each engine feeds the next."""
    random.seed(42)
    state = ResearchState()

    # 1. Question -> hypothesis
    qe = QuestionEngine(mock_mode=True)
    state = qe.run(state, query="effect of genetic variants on Alzheimer's disease")
    assert state.current_stage == Stage.HYPOTHESIS_GENERATION

    # 2. Retrieval -> literature + datasets
    re = RetrievalEngine(mock_mode=True)
    state = re.run(state)
    assert len(state.literature) >= 5
    assert len(state.datasets) >= 1

    # 3. Analysis -> statistical + bioinformatics + causal
    ae = AnalysisEngine(mock_mode=True)
    state = ae.run(state)
    assert state.statistical_results is not None
    assert state.bioinformatics_results is not None
    assert state.causal_estimates is not None

    # 4. Evidence -> grading + integration
    ee = EvidenceEngine(mock_mode=True)
    state = ee.run(state)
    assert state.integrated_evidence is not None

    # 5. Narrative -> manuscript + figures + tables
    ne = NarrativeEngine(mock_mode=True)
    state = ne.run(state)
    assert state.manuscript is not None
    assert len(state.figures) >= 1

    # 6. Execution -> review + publication
    xe = ExecutionEngine(mock_mode=True)
    state = xe.run(state)
    assert state.review_report is not None
    assert state.submission_materials is not None
    assert state.current_stage == Stage.PUBLICATION


# =============================================================================
#  Group E — Registry (Task 19)
# =============================================================================

def task_19_skills_registry():
    """skills/registry.json has 11 active skills with correct structure."""
    reg_path = ROOT / "skills" / "registry.json"
    with open(reg_path) as f:
        reg = json.load(f)

    assert reg["framework"] == "BioResearch Agent"
    assert "version" in reg
    assert "spec" in reg

    active = [s for s in reg["skills"] if s.get("status") == "active"]
    assert len(active) == 11, f"Expected 11 active skills, got {len(active)}"

    required_keys = {"name", "path", "group", "capability", "triggers", "status"}
    for skill in reg["skills"]:
        missing = required_keys - set(skill.keys())
        assert not missing, f"Skill {skill.get('name', '?')} missing keys: {missing}"

    skill_names = [s["name"] for s in active]
    expected_skills = {
        "bioresearch-introduction",
        "bioresearch-environment-check",
        "bioresearch-literature-analysis",
        "bioresearch-biomarker-discovery",
        "bioresearch-differential-expression",
        "bioresearch-pathway-enrichment",
        "bioresearch-causal-inference",
        "bioresearch-disease-case-study",
        "bioresearch-causal-evidence",
        "bioresearch-agent-router",
        "bioresearch-foundation-embeddings",
    }
    assert set(skill_names) == expected_skills, (
        f"Skill name mismatch. Got: {set(skill_names)}"
    )


# =============================================================================
#  Group F — Manifest + Governance (Task 20)
# =============================================================================

def task_20_manifest_and_governance():
    """eval/manifest.json has 7 implemented cases; .gitignore excludes raw data."""
    # --- manifest ---
    manifest_path = ROOT / "bio-research-os" / "eval" / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest["suite"] == "Biomedical Workflow Validation Suite"
    assert "framework_version" in manifest
    assert len(manifest["cases"]) == 7, (
        f"Expected 7 cases, got {len(manifest['cases'])}"
    )

    for case in manifest["cases"]:
        assert case["status"] == "implemented", (
            f"Case {case['id']} not implemented"
        )
        assert "evidence_grade" in case, f"Case {case['id']} missing evidence_grade"
        assert "workflows" in case
        assert len(case["workflows"]) >= 1

    # --- governance: .gitignore excludes raw data ---
    gitignore_path = ROOT / ".gitignore"
    with open(gitignore_path) as f:
        gi = f.read()

    assert "*.txt.gz" in gi, ".gitignore missing *.txt.gz exclusion"
    assert "*.gct.gz" in gi, ".gitignore missing *.gct.gz exclusion"
    assert "raw/" in gi, ".gitignore missing raw/ exclusion"


def task_21_foundation_embeddings():
    """Foundation-embeddings mock pipeline produces valid metrics for all 3 models."""
    demo_path = ROOT / "bio-research-os" / "demos" / "demo_foundation_embeddings.py"
    assert demo_path.exists(), "demo_foundation_embeddings.py not found"

    # Import and run the pipeline in-process (fast: 500 cells x 1000 genes)
    import importlib.util
    spec = importlib.util.spec_from_file_location("demo_fe", str(demo_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = mod.foundation_embedding_pipeline(
        n_cells=500, n_genes=1000, seed=42, noise_level=0.3
    )

    # Per-model metrics (result["metrics"] is a DataFrame)
    metrics_df = result["metrics"]
    assert len(metrics_df) == 3, f"Expected 3 models, got {len(metrics_df)}"
    model_names = set(metrics_df["model"].tolist())
    assert model_names == {"scGPT", "UCE", "scFoundation"}, (
        f"Unexpected models: {model_names}"
    )

    for _, row in metrics_df.iterrows():
        assert 0 <= row["silhouette"] <= 1, (
            f"Invalid silhouette for {row['model']}: {row['silhouette']}"
        )
        assert 0 <= row["ari"] <= 1, (
            f"Invalid ARI for {row['model']}: {row['ari']}"
        )
        assert 0 <= row["nmi"] <= 1, (
            f"Invalid NMI for {row['model']}: {row['nmi']}"
        )

    # Cross-model consistency (result["consistency"] is a DataFrame)
    consistency_df = result["consistency"]
    assert len(consistency_df) == 3, "Expected 3 pairwise comparisons"
    for _, row in consistency_df.iterrows():
        assert 0 <= row["knn_overlap"] <= 1, (
            f"Invalid kNN overlap: {row['knn_overlap']}"
        )

    # Model specs sanity
    specs = mod.MODEL_SPECS
    assert specs["scGPT"]["embedding_dim"] == 512
    assert specs["UCE"]["embedding_dim"] == 1280
    assert specs["scFoundation"]["embedding_dim"] == 512


# =============================================================================
#  Runner
# =============================================================================

TASKS = [
    task_01_biomarker_routing,
    task_02_causal_routing,
    task_03_literature_routing,
    task_04_doctor_routing,
    task_05_case_study_routing,
    task_06_unknown_intent,
    task_07_router_determinism,
    task_08_route_to_command,
    task_09_stage_enum,
    task_10_evidence_grade_enum,
    task_11_research_state_init,
    task_12_question_engine,
    task_13_retrieval_engine,
    task_14_analysis_engine,
    task_15_evidence_engine,
    task_16_narrative_engine,
    task_17_execution_engine,
    task_18_full_pipeline,
    task_19_skills_registry,
    task_20_manifest_and_governance,
    task_21_foundation_embeddings,
]

GROUPS = {
    "A": "Router",
    "B": "Core State",
    "C": "Engines",
    "D": "Pipeline",
    "E": "Registry",
    "F": "Manifest+Governance",
    "G": "Foundation",
}


def run_all() -> int:
    """Run all 21 tasks and print a summary. Returns exit code 0/1."""
    passed = 0
    failed = 0
    errors = []

    print("=" * 70)
    print("  BioResearch Agent — Benchmark-Lite (21 tasks)")
    print("=" * 70)

    for i, task in enumerate(TASKS, 1):
        name = task.__name__
        # Determine group letter
        if i <= 8:
            group = "A"
        elif i <= 11:
            group = "B"
        elif i <= 17:
            group = "C"
        elif i == 18:
            group = "D"
        elif i == 19:
            group = "E"
        elif i == 20:
            group = "F"
        else:
            group = "G"

        try:
            task()
            print(f"  [PASS] Task {i:02d} ({group}/{GROUPS[group]}): {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] Task {i:02d} ({group}/{GROUPS[group]}): {name}")
            print(f"         {type(e).__name__}: {e}")
            failed += 1
            errors.append((i, name, str(e)))

    print("-" * 70)
    print(f"  Result: {passed}/{len(TASKS)} passed, {failed} failed")
    if errors:
        print("\n  Failures:")
        for tid, tname, terr in errors:
            print(f"    Task {tid:02d} {tname}: {terr}")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
