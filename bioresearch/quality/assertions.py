"""bioresearch/quality/assertions.py — 硬编码统计断言库（不可关闭）。

把框架的 "Hard Gate" 纪律固化进代码：每条断言都有明确的通过条件、严重级
别（CRITICAL / HIGH / MEDIUM）与动作（REJECT 终止 / WARN 告警）。断言条件
为确定性纯函数，**不依赖 LLM 判断**，调用方无权在运行时修改阈值。

阈值均取自领域通行标准：
- MR 工具变量强度 F > 10（Weak-instrument 经验阈值）。
- MR-Egger 截距 p > 0.05 视为无非水平多效性（故 p < 0.05 触发告警）。
- 共定位 PP.H4 > 0.8 视为强共定位证据。
- RNA-seq 比对率 > 70%、单细胞 UMI 中位数 > 500 为常见质控红线。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Any

__all__ = [
    "AssertionStatus",
    "HardStopException",
    "AssertionSpec",
    "AssertionResult",
    "AssertionBatch",
    "BUILTIN_ASSERTIONS",
    "run_assertion",
]


class AssertionStatus(enum.Enum):
    """断言执行结果状态。"""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class HardStopException(Exception):
    """当 CRITICAL 且动作=REJECT 的断言失败时抛出，终止流水线。"""

    def __init__(self, assertion_id: str, message: str) -> None:
        self.assertion_id = assertion_id
        super().__init__(f"[HARD_STOP] {assertion_id}: {message}")


@dataclass
class AssertionSpec:
    """单条断言的规格定义。"""

    assertion_id: str
    category: str
    severity: str  # CRITICAL | HIGH | MEDIUM
    action: str  # REJECT | WARN
    message: str
    check: Callable[..., bool]  # 返回 True 表示通过

    def __post_init__(self) -> None:
        if self.severity not in ("CRITICAL", "HIGH", "MEDIUM"):
            raise ValueError(f"invalid severity: {self.severity}")
        if self.action not in ("REJECT", "WARN"):
            raise ValueError(f"invalid action: {self.action}")


@dataclass
class AssertionResult:
    """单条断言的执行结果。"""

    assertion_id: str
    status: AssertionStatus
    detail: str
    severity: str = ""

    def __repr__(self) -> str:
        return f"<{self.status.value} {self.assertion_id}: {self.detail}>"


def run_assertion(spec: AssertionSpec, **params: Any) -> AssertionResult:
    """执行单条断言。

    Args:
        spec: 断言规格。
        **params: 传给 ``spec.check`` 的命名参数（同时用于失败消息格式化）。

    Returns:
        通过返回 PASS；不通过且 action=WARN 返回 WARNING；不通过且
        action=REJECT 返回 FAIL（由 ``AssertionBatch`` 决定是否抛 ``HardStopException``）。
    """
    try:
        ok = bool(spec.check(**params))
    except Exception as exc:  # 参数缺失 / 类型错误等，视为质控失败而非静默通过
        return AssertionResult(
            spec.assertion_id, AssertionStatus.FAIL,
            f"check error: {exc}", spec.severity,
        )
    if ok:
        return AssertionResult(spec.assertion_id, AssertionStatus.PASS, "passed", spec.severity)
    if spec.action == "REJECT":
        try:
            detail = spec.message.format(**params)
        except (KeyError, IndexError):
            detail = spec.message
        return AssertionResult(spec.assertion_id, AssertionStatus.FAIL, detail, spec.severity)
    try:
        detail = spec.message.format(**params)
    except (KeyError, IndexError):
        detail = spec.message
    return AssertionResult(spec.assertion_id, AssertionStatus.WARNING, detail, spec.severity)


class AssertionBatch:
    """批量断言运行器。

    用法：
        batch = AssertionBatch(BUILTIN_ASSERTIONS)
        results = batch.run([("mr_weak_iv", {"f_stat": 8.2})])  # 触发 HardStopException
    """

    def __init__(self, specs: Dict[str, AssertionSpec]) -> None:
        self.specs = specs

    def run(
        self,
        checks: List[Tuple[str, Dict[str, Any]]],
        raise_on_reject: bool = True,
    ) -> List[AssertionResult]:
        """运行一组断言。

        Args:
            checks: ``(assertion_id, params)`` 列表。
            raise_on_reject: 若为 True，任一 REJECT 类失败立即抛 ``HardStopException``。

        Returns:
            每条断言的 ``AssertionResult`` 列表。

        Raises:
            HardStopException: 当 ``raise_on_reject`` 且存在 REJECT 类失败。
        """
        results: List[AssertionResult] = []
        for aid, params in checks:
            spec = self.specs.get(aid)
            if spec is None:
                results.append(
                    AssertionResult(aid, AssertionStatus.FAIL, f"unknown assertion {aid!r}", "UNKNOWN")
                )
                continue
            results.append(run_assertion(spec, **params))
        if raise_on_reject:
            for r in results:
                spec = self.specs.get(r.assertion_id)
                if r.status == AssertionStatus.FAIL and spec is not None and spec.action == "REJECT":
                    raise HardStopException(r.assertion_id, r.detail)
        return results


# --------------------------------------------------------------------------- #
# 内置断言库（阈值见模块 docstring）
# --------------------------------------------------------------------------- #
BUILTIN_ASSERTIONS: Dict[str, AssertionSpec] = {
    "mr_weak_iv": AssertionSpec(
        assertion_id="mr_weak_iv",
        category="mendelian_randomization",
        severity="CRITICAL",
        action="REJECT",
        message="弱工具变量 (F={f_stat:.2f} < 10)。拒绝执行 IVW，建议放宽 clumping 阈值或改用 MR-RAPS。",
        check=lambda f_stat: f_stat >= 10.0,
    ),
    "mr_pleiotropy": AssertionSpec(
        assertion_id="mr_pleiotropy",
        category="mendelian_randomization",
        severity="HIGH",
        action="WARN",
        message="MR-Egger 截距显著 (p={egger_p:.3f})，提示水平多效性。建议增加 CAUSE 验证并在讨论中披露。",
        check=lambda egger_p: egger_p >= 0.05,
    ),
    "coloc_weak": AssertionSpec(
        assertion_id="coloc_weak",
        category="colocalization",
        severity="MEDIUM",
        action="WARN",
        message="共定位证据不足 (PP.H4={h4:.2f} < 0.8)。建议尝试 SuSiE 精细定位或 TWAS 补充。",
        check=lambda h4: h4 >= 0.8,
    ),
    "rnaseq_low_mapping": AssertionSpec(
        assertion_id="rnaseq_low_mapping",
        category="rnaseq",
        severity="CRITICAL",
        action="REJECT",
        message="RNA-seq 比对率过低 ({rate:.1%} < 70%)。拒绝下游分析，请检查数据质量。",
        check=lambda rate: rate >= 0.70,
    ),
    "scrnaseq_low_umi": AssertionSpec(
        assertion_id="scrnaseq_low_umi",
        category="single_cell",
        severity="CRITICAL",
        action="REJECT",
        message="单细胞 UMI 中位数过低 ({umi} < 500)。拒绝分析，建议提高测序深度。",
        check=lambda umi: umi >= 500,
    ),
    "gwas_small_sample": AssertionSpec(
        assertion_id="gwas_small_sample",
        category="mendelian_randomization",
        severity="MEDIUM",
        action="WARN",
        message="GWAS 样本量偏小 (n={n})，统计功效有限，结论需谨慎解读。",
        check=lambda n: n >= 1000,
    ),
    "multiple_testing_unadjusted": AssertionSpec(
        assertion_id="multiple_testing_unadjusted",
        category="statistics",
        severity="HIGH",
        action="WARN",
        message="多重检验校正后 q={q_value:.3f} > 0.05，需谨慎；建议报告 BH 校正 q 值。",
        check=lambda q_value: q_value <= 0.05,
    ),
    "finemapping_low_pp": AssertionSpec(
        assertion_id="finemapping_low_pp",
        category="fine_mapping",
        severity="MEDIUM",
        action="WARN",
        message="精细定位可信集 PP={pp:.2f} < 0.8，因果变异定位不确定。",
        check=lambda pp: pp >= 0.8,
    ),
}
