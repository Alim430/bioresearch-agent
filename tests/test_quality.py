"""Tests for ``bioresearch.quality`` (hard QC + governance + audit).

These tests verify the framework's "Hard Gate" discipline and data-governance
interceptor actually fire:
- weak instrument variable (F < 10) terminates the pipeline via ``HardStopException``;
- controlled-access / individual-level sources are blocked (ADNI, UKB-PPP, MetaBrain,
  deCODE, personal_genome) while public sources pass;
- the audit hash-chain is internally consistent and continuous across sessions.
"""

import hashlib
import json

from bioresearch.quality.assertions import (
    AssertionBatch,
    BUILTIN_ASSERTIONS,
    HardStopException,
    AssertionStatus,
)
from bioresearch.quality.governance import (
    BLOCKED_DATA_SOURCES,
    DataAccessBlockedError,
    validate_data_request,
)
from bioresearch.quality.audit import AuditTrail, _ZERO_HASH


def test_mr_weak_iv_rejects():
    batch = AssertionBatch(BUILTIN_ASSERTIONS)
    # f_stat below 10 -> HardStopException
    raised = False
    try:
        batch.run([("mr_weak_iv", {"f_stat": 8.2})])
    except HardStopException as e:
        raised = True
        assert e.assertion_id == "mr_weak_iv"
    assert raised, "weak IV (F<10) must raise HardStopException"
    # f_stat >= 10 -> passes, no raise
    results = batch.run([("mr_weak_iv", {"f_stat": 12.0})], raise_on_reject=True)
    assert results[0].status == AssertionStatus.PASS


def test_governance_blocks_controlled_sources():
    blocked = ["ADNI", "UKB-PPP", "UKB-PPP v2", "MetaBrain", "deCODE", "personal_genome"]
    for src in blocked:
        raised = False
        try:
            validate_data_request(src)
        except DataAccessBlockedError:
            raised = True
        assert raised, f"controlled source {src!r} must be blocked"
    # allowed public / summary-level sources pass without error
    validate_data_request("IEU OpenGWAS")
    validate_data_request("GTEx v8 brain eQTL")
    # every key in BLOCKED_DATA_SOURCES is actually enforced
    for key in BLOCKED_DATA_SOURCES:
        raised = False
        try:
            validate_data_request(key)
        except DataAccessBlockedError:
            raised = True
        assert raised, f"blacklist key {key!r} not enforced"


def test_audit_chain_continuous(tmp_path):
    p = tmp_path / "audit.jsonl"
    trail = AuditTrail(p)
    trail.log("STAGE_START", stage="IDEATION")
    trail.log("ASSERTION_CHECK", assertion="mr_weak_iv", passed=True)

    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    recs = [json.loads(l) for l in lines]

    # first record chains from the zero hash
    assert recs[0]["prev_hash"] == _ZERO_HASH
    # recompute each chain_hash to prove integrity (mirrors audit.py logic)
    for rec in recs:
        payload = json.dumps(
            {k: v for k, v in rec.items() if k not in ("chain_hash", "prev_hash")},
            sort_keys=True,
            ensure_ascii=False,
        )
        expected = hashlib.sha256(
            (rec["prev_hash"] + "|" + payload).encode("utf-8")
        ).hexdigest()
        assert rec["chain_hash"] == expected, "audit chain broken"

    # reopening the same file continues the chain from the last hash
    trail2 = AuditTrail(p)
    assert trail2._prev_hash == recs[-1]["chain_hash"]
    assert trail2.session_summary()["records"] == 2
