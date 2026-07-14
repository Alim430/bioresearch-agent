"""bioresearch.quality — 硬性质控与审计（确定性，无自主推理）。

提供三部分能力，把框架的 "Hard Gate" 与可复现性纪律固化进代码：
1. ``assertions`` — 硬编码统计断言库（不可关闭）：F-stat<10 拒绝、Egger 截距、
   coloc H4、RNA-seq 比对率、scRNA UMI 等，配 ``AssertionBatch`` 批量运行器。
2. ``governance`` — 数据治理拦截器：受控访问 / 个体级数据（ADNI / UKB-PPP /
   MetaBrain / deCODE）硬黑名单，对齐 ``DATA_GOVERNANCE.md``；附 ``DataProvenance``
   血缘记录。
3. ``audit`` — 链式哈希审计追踪（JSONL），支持跨会话续链与防篡改校验。

这些模块完全依赖确定性纯函数与标准库，不调用任何 LLM，不参与科研决策。
"""

from .assertions import (
    AssertionStatus,
    HardStopException,
    AssertionSpec,
    AssertionResult,
    AssertionBatch,
    BUILTIN_ASSERTIONS,
    run_assertion,
)
from .governance import (
    DataAccessBlockedError,
    BLOCKED_DATA_SOURCES,
    LICENSE_TIER,
    validate_data_request,
    compute_sha256,
    DataProvenance,
)
from .audit import AuditTrail

__all__ = [
    "AssertionStatus",
    "HardStopException",
    "AssertionSpec",
    "AssertionResult",
    "AssertionBatch",
    "BUILTIN_ASSERTIONS",
    "run_assertion",
    "DataAccessBlockedError",
    "BLOCKED_DATA_SOURCES",
    "LICENSE_TIER",
    "validate_data_request",
    "compute_sha256",
    "DataProvenance",
    "AuditTrail",
]
