"""Deterministic tests for the rule-based Agent Router v0 (no LLM, no network)."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bioresearch.router import classify_intent, route_to_command, AVAILABLE_ROUTES  # noqa: E402


def test_biomarker_routing():
    r = classify_intent("find biomarkers for Parkinson's disease using GSE7621")
    assert r["route"] == "biomarker"
    assert r["confidence"] > 0
    assert "biomarker" in r["matched_keywords"] or "geo dataset" in r["matched_keywords"]


def test_literature_routing():
    r = classify_intent("do a literature review on microglia in Alzheimer's disease and find research gaps")
    assert r["route"] == "literature"
    assert r["confidence"] >= 0.5


def test_causal_routing():
    r = classify_intent("test the causal effect of BMI on type 2 diabetes with Mendelian randomization")
    assert r["route"] == "causal"
    assert "mendelian randomization" in r["matched_keywords"]


def test_case_study_routing():
    r = classify_intent("run a disease case study validation on real data to benchmark the framework")
    assert r["route"] == "case-study"


def test_doctor_routing():
    r = classify_intent("validate the installation and check dependencies")
    assert r["route"] == "doctor"


def test_unknown_intent():
    r = classify_intent("what is the meaning of life")
    assert r["route"] == "unknown"
    assert r["confidence"] == 0.0
    assert r["suggestion"] == AVAILABLE_ROUTES


def test_deterministic():
    a = classify_intent("Mendelian randomization BMI diabetes")
    b = classify_intent("Mendelian randomization BMI diabetes")
    assert a == b


def test_confidence_is_share_of_hits():
    # Only causal keywords -> confidence 1.0
    r = classify_intent("mendelian randomization")
    assert r["route"] == "causal"
    assert r["confidence"] == 1.0


def test_tie_breaks_to_more_specific_route():
    # "exposure" matches causal; also "gene expression"? no. Use a phrase that
    # could match both biomarker and causal weakly; priority should pick causal.
    r = classify_intent("exposure and outcome analysis")
    assert r["route"] == "causal"


def test_route_to_command():
    assert "literature" in route_to_command("literature")
    assert "biomarker" in route_to_command("biomarker")
    assert "causal" in route_to_command("causal")
    assert "case_study_pd.py" in route_to_command("case-study")
    assert "doctor" in route_to_command("doctor")
    assert route_to_command("unknown") == "bioresearch --help"


if __name__ == "__main__":
    # Minimal runner without pytest installed
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
