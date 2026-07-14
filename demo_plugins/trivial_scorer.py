"""demo_plugins/trivial_scorer.py — 纯合成示例评分器（DEMO ONLY，零真实数据）。

本文件是 ``EvidenceScorer`` 接口的**最小可运行示例**，用于演示第三方 / 私有
评分器如何接入公开框架。它：

- 只用**伪造（fake）证据层**（固定 / 随机值，seed=42），不含任何 AD-VCP / VCIS
  内部逻辑，也不含任何真实基因、真实队列或发表级数据；
- 实现 ``EvidenceScorer`` 的四个契约方法（name / supported_layers /
  validate_layers / score）；
- 可通过 ``PluginRegistry.register()`` 或在私有发行包中以 ``entry_points`` 声明
  接入框架。

请勿将其误认为真实评分体系。真实评分（如 AD-VCP 的 VCIS）在私有仓实现，且
绝不进入本公开仓库。
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from bioresearch.scorer.base import EvidenceLayer, EvidenceScorer, ScoredGene

DEMO_SEED: int = 42


class TrivialDemoScorer(EvidenceScorer):
    """演示用评分器：对通过质控的层做确定性均值聚合（仅用于展示接口）。"""

    def __init__(self, seed: int = DEMO_SEED) -> None:
        self._seed = seed

    @property
    def name(self) -> str:
        return "TrivialDemoScorer"

    @property
    def supported_layers(self) -> List[str]:
        return ["genetic", "functional", "population"]

    def validate_layers(self, layers: List[EvidenceLayer]) -> bool:
        if not layers:
            return False
        return any(l.qc_passed for l in layers)

    def _synthesize(self, gene: str) -> List[EvidenceLayer]:
        """生成确定性伪造证据层（seed=42，零真实数据）。"""
        rng = random.Random(f"{gene}:{self._seed}")
        return [
            EvidenceLayer(
                layer_id=lid,
                source="SYNTHETIC_DEMO",
                confidence=round(rng.uniform(0.3, 0.9), 4),
                direction="neutral",
                qc_passed=True,
            )
            for lid in self.supported_layers
        ]

    def score(
        self,
        gene: str,
        evidence_layers: Optional[List[EvidenceLayer]] = None,
        context: Optional[Dict] = None,
    ) -> ScoredGene:
        if evidence_layers is None:
            evidence_layers = self._synthesize(gene)
        if not self.validate_layers(evidence_layers):
            raise ValueError(f"[{self.name}] insufficient evidence for {gene!r}")
        passed = [l for l in evidence_layers if l.qc_passed]
        total = round(sum(l.confidence for l in passed) / len(passed), 4)
        lo = round(max(0.0, total - 0.05), 4)
        hi = round(min(1.0, total + 0.05), 4)
        layer_conf = {l.layer_id: l.confidence for l in passed}
        return ScoredGene(
            gene_symbol=gene,
            ensemble_id=(context or {}).get("ensemble_id", "NA"),
            total_score=total,
            layer_scores=layer_conf,
            confidence_interval=(lo, hi),
            rank_stability=1.0,
            layer_confidence=layer_conf,
        )


def demo() -> ScoredGene:
    """注册并评分一个示例基因（使用合成证据），返回 ``ScoredGene``。"""
    from bioresearch.scorer.registry import PluginRegistry

    reg = PluginRegistry()
    reg.register(TrivialDemoScorer(), set_default=True)
    return reg.default().score("DEMO_GENE")


if __name__ == "__main__":
    result = demo()
    print(result)
