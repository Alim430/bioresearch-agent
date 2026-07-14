"""bioresearch/scorer/registry.py — 简单内存插件注册表。

提供进程内评分器注册 / 获取 / 列出 / 设默认。保持轻量、无外部依赖；
未来如需 ``entry_points`` 自动发现，可在此基础上扩展，而不改变调用契约。

线程安全说明：注册通常发生在启动期，运行期只读；本实现未加锁，若需要在
多线程运行时动态注册，请在外层加锁。
"""

from __future__ import annotations

from importlib.metadata import entry_points as _entry_points
from typing import Dict, List, Optional

from .base import EvidenceScorer

__all__ = ["PluginRegistry"]


def _load_scorer_entry_points(group: str = "bioresearch.scorers"):
    """Return the entry points in ``group`` across Python versions."""
    try:
        return list(_entry_points(group=group))
    except TypeError:  # Python < 3.10
        return list(_entry_points().get(group, []))


class PluginRegistry:
    """进程内 EvidenceScorer 注册表。"""

    def __init__(self) -> None:
        self._registry: Dict[str, EvidenceScorer] = {}
        self._default: Optional[str] = None

    def register(self, scorer: EvidenceScorer, set_default: bool = False) -> None:
        """注册一个评分器实例。

        Args:
            scorer: 实现 ``EvidenceScorer`` 的实例。
            set_default: 若为 True，将其设为默认评分器。
        """
        self._registry[scorer.name] = scorer
        if set_default or self._default is None:
            self._default = scorer.name

    def get(self, name: str) -> EvidenceScorer:
        """按名称获取评分器。"""
        if name not in self._registry:
            raise KeyError(f"Scorer {name!r} not registered. Available: {self.list()}")
        return self._registry[name]

    def default(self) -> EvidenceScorer:
        """获取当前默认评分器。"""
        if self._default is None:
            raise RuntimeError("No scorer registered yet.")
        return self._registry[self._default]

    def list(self) -> List[str]:
        """列出所有已注册评分器名称。"""
        return list(self._registry.keys())

    def set_default(self, name: str) -> None:
        """显式设置默认评分器。"""
        if name not in self._registry:
            raise KeyError(f"Scorer {name!r} not registered.")
        self._default = name

    @classmethod
    def discover_entry_points(cls, group: str = "bioresearch.scorers") -> "PluginRegistry":
        """扫描已安装的 ``entry_points`` 并注册发现的评分器插件。

        第三方 / 私有评分器可在其 ``pyproject.toml`` 声明::

            [project.entry-points."bioresearch.scorers"]
            my_scorer = my_pkg.module:MyScorerClass

        其中 ``MyScorerClass`` 必须可无参实例化且实现 ``EvidenceScorer``。

        Returns:
            一个已注册所有被发现评分器的 ``PluginRegistry``（未发现则为空表）。
        """
        reg = cls()
        for ep in _load_scorer_entry_points(group):
            try:
                scorer_cls = ep.load()
                reg.register(scorer_cls())
            except Exception:
                # 单个损坏插件不得连累其他插件的发现
                continue
        return reg
