"""bioresearch/quality/governance.py — 数据治理拦截器（对齐 DATA_GOVERNANCE.md）。

把仓库的 ``DATA_GOVERNANCE.md`` 软约束固化为**硬代码**拦截：任何受控访问 /
个体级数据来源（MetaBrain、UKB-PPP、ADNI、deCODE）或个人基因组数据在被
加载前即被拒绝，并返回明确权限错误。框架只处理公开、去标识化或汇总级数据。

与文档保持一致（DATA_GOVERNANCE.md §1 Tier 表 Excluded 行 + 隐私护栏）。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

__all__ = [
    "DataAccessBlockedError",
    "BLOCKED_DATA_SOURCES",
    "LICENSE_TIER",
    "validate_data_request",
    "compute_sha256",
    "DataProvenance",
]


class DataAccessBlockedError(RuntimeError):
    """当请求受控访问 / 个体级数据时抛出。"""

    def __init__(self, source: str, reason: str) -> None:
        self.source = source
        super().__init__(f"[DATA_GOVERNANCE] {source}: {reason}")


# 名称使用小写归一化键，匹配 DATA_GOVERNANCE.md §1 的 Excluded 行 + 隐私护栏。
BLOCKED_DATA_SOURCES: Dict[str, str] = {
    "metabrain": "Controlled-access individual-level brain RNA-seq; DUA; re-identification risk.",
    "ukb-ppp": "UK Biobank controlled access; framework uses IEU OpenGWAS summary data instead.",
    "adni": "ADNI data-use agreement; individual-level data excluded.",
    "decode": "Proprietary/controlled terms (conservative exclusion).",
    "personal_genome": "Personal genome data involves privacy; framework prohibits processing.",
}

LICENSE_TIER: Dict[str, str] = {
    "metabrain": "controlled",
    "ukb-ppp": "controlled",
    "adni": "controlled",
    "decode": "controlled",
    "personal_genome": "private",
}


def _normalize(name: str) -> str:
    return name.strip().lower()


def validate_data_request(source: str) -> None:
    """验证数据来源是否被允许。

    Args:
        source: 数据来源名称（任意大小写 / 可含版本后缀，如 "UKB-PPP v2"）。

    Raises:
        DataAccessBlockedError: 当来源属于受控访问 / 个体级 / 隐私类黑名单。
    """
    key = _normalize(source)
    if key in BLOCKED_DATA_SOURCES:
        raise DataAccessBlockedError(source, BLOCKED_DATA_SOURCES[key])
    # 子串护栏：覆盖 "UKB-PPP v2" -> "ukb-ppp" 等情况
    for blocked_key, reason in BLOCKED_DATA_SOURCES.items():
        if blocked_key in key or key in blocked_key:
            raise DataAccessBlockedError(source, reason)


def compute_sha256(path) -> str:
    """计算文件 SHA-256（用于数据血缘 / 可复现性）。"""
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DataProvenance:
    """数据血缘记录（可复现性包的一部分）。"""

    source: str
    license_tier: str
    sha256: str = ""
    version: str = ""
    fetched_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        """序列化为字典。"""
        return {
            "source": self.source,
            "license_tier": self.license_tier,
            "sha256": self.sha256,
            "version": self.version,
            "fetched_at": self.fetched_at,
            "notes": self.notes,
        }
