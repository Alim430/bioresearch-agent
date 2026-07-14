"""bioresearch/scorer/base.py — 通用证据评分器抽象接口（框架核心，无自主推理）。

本模块定义公开框架唯一保留的评分抽象：``EvidenceScorer``。它**不实现任何
自主科研决策**，仅提供可插拔的证据分级契约。具体评分逻辑（如 AD-VCP 的
VCIS）作为该接口的**私有插件**实现，不进入本公开框架的分发。

设计原则：
- 纯确定性计算，不调用任何 LLM / 外部模型。
- 所有输入证据层必须携带 ``qc_passed`` 标记，未通过质控的层默认不参与评分。
- 评分结果附带置信区间与排名稳定性，便于可复现审计。
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["EvidenceLayer", "LayerConfidence", "ScoredGene", "EvidenceScorer"]


@dataclass
class EvidenceLayer:
    """单一层证据。

    Attributes:
        layer_id: 证据层标识，如 ``"genetic"`` / ``"functional"`` / ``"population"``。
        source: 数据来源描述（如 ``"IEU OpenGWAS"``）。
        confidence: 该层置信度，取值 [0, 1]。
        direction: 效应方向，取值 ``"protective"`` / ``"risk"`` / ``"neutral"``。
        raw_data: 原始统计量（beta / p / n 等），供审计回溯。
        qc_passed: 该层是否通过硬性质控（见 ``bioresearch.quality.assertions``）。
    """

    layer_id: str
    source: str
    confidence: float
    direction: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    qc_passed: bool = True

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if self.direction not in ("protective", "risk", "neutral"):
            raise ValueError(f"invalid direction: {self.direction!r}")


@dataclass
class LayerConfidence:
    """单层的置信元信息。"""

    layer_id: str
    confidence: float
    qc_passed: bool
    n_evidence: int = 1


@dataclass
class ScoredGene:
    """评分后的基因。

    Attributes:
        gene_symbol: 基因符号。
        ensemble_id: Ensembl 基因 ID（缺失时为 ``"NA"``）。
        total_score: 综合评分（加权几何均值，[0, 1]）。
        layer_scores: 各通过质控层的贡献评分。
        confidence_interval: Bootstrap 95% 置信区间 ``(lower, upper)``。
        rank_stability: 排名稳定性，取值 [0, 1]，越接近 1 越稳定。
        layer_confidence: 各层的置信度快照。
    """

    gene_symbol: str
    ensemble_id: str
    total_score: float
    layer_scores: Dict[str, float] = field(default_factory=dict)
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    rank_stability: float = 0.0
    layer_confidence: Dict[str, float] = field(default_factory=dict)


class EvidenceScorer(abc.ABC):
    """通用证据评分器抽象基类 — 公开框架唯一保留的接口。

    实现者只需提供 ``name`` / ``supported_layers`` / ``score`` / ``validate_layers``
    四个契约方法；默认层权重由 ``get_layer_weights`` 给出，可覆盖。
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """评分器名称（同时用作插件注册键）。"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def supported_layers(self) -> List[str]:
        """支持的证据层 ID 列表。"""
        raise NotImplementedError

    @abc.abstractmethod
    def score(
        self,
        gene: str,
        evidence_layers: List[EvidenceLayer],
        context: Optional[Dict] = None,
    ) -> ScoredGene:
        """对单个基因进行评分。

        Args:
            gene: 基因符号。
            evidence_layers: 该基因的所有证据层。
            context: 可选上下文（如 ``{"ensemble_id": "ENSG...", "disease": "AD"}``）。

        Returns:
            ScoredGene 对象。

        Raises:
            ValueError: 当 ``validate_layers`` 返回 False（证据不足或无效）。
        """
        raise NotImplementedError

    @abc.abstractmethod
    def validate_layers(self, layers: List[EvidenceLayer]) -> bool:
        """验证输入证据层是否满足最低要求（至少一层通过质控）。"""
        raise NotImplementedError

    def get_layer_weights(self) -> Dict[str, float]:
        """获取默认层权重（等权）。实现者可覆盖为领域特定权重。"""
        layers = self.supported_layers
        if not layers:
            return {}
        return {layer: 1.0 / len(layers) for layer in layers}
