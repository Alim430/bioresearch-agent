"""Tests for ``bioresearch.scorer`` (B+C compliant subset, deterministic, no LLM).

These tests verify the public framework's evidence-scoring contract:
- reproducibility under a fixed seed,
- score output shape / ranges,
- the ``validate_layers`` gate (rejects evidence with no qc_passed layer),
- the in-memory ``PluginRegistry`` mechanics.
"""

from bioresearch.scorer.base import EvidenceLayer, EvidenceScorer, ScoredGene
from bioresearch.scorer.default import DefaultMultiModalScorer
from bioresearch.scorer.registry import PluginRegistry


def _make_layers():
    """Three qc_passed evidence layers spanning supported layer IDs."""
    return [
        EvidenceLayer(layer_id="genetic", source="IEU OpenGWAS", confidence=0.8,
                      direction="risk", qc_passed=True),
        EvidenceLayer(layer_id="functional", source="GTEx v8", confidence=0.7,
                      direction="risk", qc_passed=True),
        EvidenceLayer(layer_id="population", source="FinnGen", confidence=0.6,
                      direction="risk", qc_passed=True),
    ]


def test_determinism_seed42():
    s1 = DefaultMultiModalScorer(seed=42)
    s2 = DefaultMultiModalScorer(seed=42)
    g1 = s1.score("TREM2", _make_layers())
    g2 = s2.score("TREM2", _make_layers())
    assert g1.total_score == g2.total_score
    assert g1.confidence_interval == g2.confidence_interval
    assert g1.rank_stability == g2.rank_stability


def test_score_output_shape():
    s = DefaultMultiModalScorer(seed=42)
    g = s.score("TREM2", _make_layers(), context={"ensemble_id": "ENSG00000133489"})
    assert isinstance(g, ScoredGene)
    assert 0.0 <= g.total_score <= 1.0
    assert len(g.confidence_interval) == 2
    assert g.confidence_interval[0] <= g.confidence_interval[1]
    assert 0.0 <= g.rank_stability <= 1.0
    assert g.ensemble_id == "ENSG00000133489"
    assert set(g.layer_scores.keys()) == {"genetic", "functional", "population"}


def test_validate_layers_requires_qc_passed():
    s = DefaultMultiModalScorer(seed=42)
    # all qc_passed=False -> validate returns False, score raises
    bad = [EvidenceLayer(layer_id="genetic", source="x", confidence=0.9,
                         direction="risk", qc_passed=False)]
    assert s.validate_layers(bad) is False
    raised = False
    try:
        s.score("GENE", bad)
    except ValueError:
        raised = True
    assert raised, "score() must raise ValueError when no qc_passed layer"
    # empty -> False
    assert s.validate_layers([]) is False


def test_registry_register_and_default():
    reg = PluginRegistry()
    a = DefaultMultiModalScorer(seed=1)
    b = DefaultMultiModalScorer(seed=2)
    reg.register(a, set_default=True)
    reg.register(b, set_default=True)
    # name is the registry key; duplicate names overwrite
    assert reg.list() == ["DefaultMultiModalScorer"]
    assert reg.default().name == "DefaultMultiModalScorer"
    assert reg.get("DefaultMultiModalScorer") is b
    raised = False
    try:
        reg.get("DoesNotExist")
    except KeyError:
        raised = True
    assert raised, "get() must raise KeyError for unknown scorer"
