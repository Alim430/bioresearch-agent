"""bioresearch.scorer — 通用证据评分插件接口（公开框架核心，无自主推理）。

仅提供 ``EvidenceScorer`` 抽象契约 + 默认实现 ``DefaultMultiModalScorer`` +
内存插件注册表 ``PluginRegistry``。具体评分体系（如 AD-VCP 的 VCIS）作为该
接口的**私有插件**实现，不随本公开框架分发。

本包不包含任何 LLM 调用或自主科研决策；评分是完全确定性的数值聚合。
"""

from .base import EvidenceLayer, EvidenceScorer, LayerConfidence, ScoredGene
from .default import DefaultMultiModalScorer
from .registry import PluginRegistry

__all__ = [
    "EvidenceLayer",
    "EvidenceScorer",
    "LayerConfidence",
    "ScoredGene",
    "DefaultMultiModalScorer",
    "PluginRegistry",
]
