"""bioresearch/scorer/default.py — DefaultMultiModalScorer（确定性加权评分，无 LLM）。

默认评分器：对通过质控的证据层做**加权几何均值**（各层置信度的几何聚合），
并通过 Bootstrap 重采样估计 95% 置信区间与排名稳定性。整个流程为纯确定性
计算（固定随机种子），不依赖任何语言模型或外部推理。

注意：几何均值要求各层置信度严格为正；本实现对 0 置信度做 ``1e-6`` 下截断，
避免对数域出现负无穷。
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from .base import EvidenceLayer, EvidenceScorer, ScoredGene

DEFAULT_SEED: int = 42
N_BOOTSTRAP: int = 200
_EPS = 1e-6


class DefaultMultiModalScorer(EvidenceScorer):
    """通用多模态证据评分器（默认实现）。"""

    def __init__(
        self,
        layer_weights: Optional[Dict[str, float]] = None,
        seed: int = DEFAULT_SEED,
    ) -> None:
        """初始化。

        Args:
            layer_weights: 可选的层权重覆盖（键为 layer_id）。未指定层取等权。
            seed: Bootstrap 重采样的固定随机种子（保证可复现）。
        """
        self._layer_weights = layer_weights or {}
        self._seed = seed

    @property
    def name(self) -> str:
        return "DefaultMultiModalScorer"

    @property
    def supported_layers(self) -> List[str]:
        return ["genetic", "functional", "population", "single_cell", "literature"]

    def get_layer_weights(self) -> Dict[str, float]:
        if self._layer_weights:
            return dict(self._layer_weights)
        return super().get_layer_weights()

    def validate_layers(self, layers: List[EvidenceLayer]) -> bool:
        if not layers:
            return False
        return any(l.qc_passed for l in layers)

    def score(
        self,
        gene: str,
        evidence_layers: List[EvidenceLayer],
        context: Optional[Dict] = None,
    ) -> ScoredGene:
        if not self.validate_layers(evidence_layers):
            raise ValueError(
                f"[{self.name}] insufficient/invalid evidence layers for {gene!r}: "
                f"need >=1 qc_passed layer."
            )

        weights = self.get_layer_weights()
        passed = [l for l in evidence_layers if l.qc_passed]

        # 仅在现有层上归一化权重，避免缺失层稀释分数
        present = [l.layer_id for l in passed]
        w_sum = sum(weights.get(lid, 1.0 / len(self.supported_layers)) for lid in present) or 1.0

        layer_scores: Dict[str, float] = {}
        layer_conf: Dict[str, float] = {}
        log_sum = 0.0
        for l in passed:
            w = weights.get(l.layer_id, 1.0 / len(self.supported_layers)) / w_sum
            c = round(l.confidence, 4)
            layer_scores[l.layer_id] = c
            layer_conf[l.layer_id] = c
            log_sum += w * math.log(max(l.confidence, _EPS))

        total = math.exp(log_sum)

        # Bootstrap：对通过质控的层做有放回重采样，估计 CI 与稳定性
        rng = random.Random(self._seed)
        confs = [max(l.confidence, _EPS) for l in passed]
        norm_w = [
            weights.get(l.layer_id, 1.0 / len(self.supported_layers)) / w_sum
            for l in passed
        ]
        boots: List[float] = []
        for _ in range(N_BOOTSTRAP):
            idx = [rng.randrange(len(passed)) for _ in passed]
            ls = sum(norm_w[i] * math.log(confs[i]) for i in idx)
            boots.append(math.exp(ls))
        boots.sort()
        n = len(boots)
        lo = boots[max(0, int(0.025 * n))]
        hi = boots[min(n - 1, int(0.975 * n))]
        ci = (round(lo, 4), round(hi, 4))
        rank_stability = round(1.0 - (max(boots) - min(boots)), 4)

        return ScoredGene(
            gene_symbol=gene,
            ensemble_id=(context or {}).get("ensemble_id", "NA"),
            total_score=round(total, 4),
            layer_scores=layer_scores,
            confidence_interval=ci,
            rank_stability=rank_stability,
            layer_confidence=layer_conf,
        )
