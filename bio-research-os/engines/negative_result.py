"""
engines/negative_result.py
===========================
Negative-result engine (honest null handling).

The framework's Hard Gate discipline requires that non-significant / null findings be
surfaced explicitly rather than silently dropped. This module classifies each tested
result into SIGNIFICANT / NULL / INCONCLUSIVE and emits a structured ``NullReport`` so
reviewers can see exactly what was tested and what did NOT reach significance.

This is pure deterministic bookkeeping — no LLM, no autonomous judgment. The
classification rule is explicit and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_SIGNIFICANT = "SIGNIFICANT"
_NULL = "NULL"
_INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class NullReport:
    """结构化阴性结果报告。"""

    total: int = 0
    significant: int = 0
    null: int = 0
    inconclusive: int = 0
    null_items: List[Dict[str, Any]] = field(default_factory=list)
    raw: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "significant": self.significant,
            "null": self.null,
            "inconclusive": self.inconclusive,
            "null_items": self.null_items,
            "raw": self.raw,
        }


class NegativeResultEngine:
    """将一组统计结果显式分类为显著 / 阴性 / 不确定。"""

    def __init__(self, alpha: float = 0.05, cross_zero_is_null: bool = True) -> None:
        """
        Args:
            alpha: 显著性阈值（默认 0.05）。
            cross_zero_is_null: 若提供置信区间且其跨越 0，即使 p ≤ alpha 也判为不确定。
        """
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")
        self.alpha = alpha
        self.cross_zero_is_null = cross_zero_is_null

    def classify(self, item: Dict[str, Any]) -> str:
        """对单个结果分类。

        Args:
            item: 必须含 ``pvalue``（或 ``p``）；可选 ``ci_low`` / ``ci_high`` / ``effect``。

        Returns:
            ``SIGNIFICANT`` / ``NULL`` / ``INCONCLUSIVE``。
        """
        p = item.get("pvalue", item.get("p"))
        if p is None:
            raise ValueError(f"item missing 'pvalue'/'p': {item!r}")
        if p > self.alpha:
            return _NULL
        # p <= alpha: 若提供 CI 且跨越 0，则不确定
        ci_low = item.get("ci_low")
        ci_high = item.get("ci_high")
        if self.cross_zero_is_null and ci_low is not None and ci_high is not None:
            if ci_low * ci_high < 0:  # 跨 0
                return _INCONCLUSIVE
        return _SIGNIFICANT

    def run(self, items: List[Dict[str, Any]]) -> NullReport:
        """分类整组结果并生成报告（阴性结果单独列出，不静默丢弃）。"""
        report = NullReport(total=len(items))
        for item in items:
            label = self.classify(item)
            if label == _SIGNIFICANT:
                report.significant += 1
            elif label == _NULL:
                report.null += 1
                report.null_items.append(item)
            else:
                report.inconclusive += 1
            report.raw.append({"item": item, "label": label})
        return report
