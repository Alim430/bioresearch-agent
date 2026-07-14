# Golden Path 矩阵（标准流程 + 不可绕过硬性质控）

> 本文件把各领域的**标准分析流程**与 `bioresearch/quality/assertions.py` 的**不可关闭硬性质控点**一一对齐。
> 每个黄金流程都有明确的"不可绕过质控"——任何一步未通过，流水线必须终止（`REJECT`）或告警（`WARN`），
> 不允许静默绕过。所有阈值均取自领域通行标准，详见 `quality/assertions.py` 模块 docstring。
> 对应能力以 Agent Skill 形式提供（见 [`skills/README.md`](../skills/README.md)）。

| # | 领域 | 黄金流程 | 关键步骤 | 不可绕过质控（断言 ID → 阈值） | 对应 Skill |
|---|------|----------|----------|-------------------------------|-----------|
| 1 | Bulk RNA-seq | ENCODE RNA-seq | 比对 → 定量 → DEG → 富集 | `rnaseq_low_mapping` → 比对率 ≥ 70%（REJECT）；`multiple_testing_unadjusted` → BH q ≤ 0.05（WARN） | `bioresearch-differential-expression` / `bioresearch-pathway-enrichment` |
| 2 | 变异 calling | GATK Best Practices | 比对 → BQSR → HaplotypeCaller → VQSR | `gwas_small_sample` 不适用；以比对率与覆盖度为前置（复用 `rnaseq_low_mapping` 思路） | — |
| 3 | 孟德尔随机化 | MR-Base / TwoSampleMR | 工具变量筛选 → IVW → 敏感性 | `mr_weak_iv` → F ≥ 10（REJECT）；`mr_pleiotropy` → Egger p ≥ 0.05（WARN）；`gwas_small_sample` → n ≥ 1000（WARN） | `bioresearch-causal-inference` |
| 4 | 共定位 | Coloc / SuSiE | 汇总统计对齐 → 共定位 → 精细定位 | `coloc_weak` → PP.H4 ≥ 0.8（WARN）；`finemapping_low_pp` → 可信集 PP ≥ 0.8（WARN） | `bioresearch-causal-evidence` |
| 5 | 跨祖先 MR | CAUSE / MRMix | GWAS 协调 → 多效性建模 → 可移植性 | `mr_weak_iv`、`mr_pleiotropy`、`gwas_small_sample`（同上）+ 祖先 LD 参考校验 | `bioresearch-ancestry-aware-mr` / `bioresearch-gwas-harmonization` / `bioresearch-ld-reference-management` |
| 6 | 单细胞转录组 | scRNA-seq 标准 | 比对/计数 → 质控 → 聚类 → 差异 | `scrnaseq_low_umi` → 中位 UMI ≥ 500（REJECT） | `bioresearch-foundation-embeddings`（嵌入层） |
| 7 | 文献综述 | PubMed 检索 + 共现图 | 检索 → 实体抽取 → 共现 → gap | 无统计断言；以 `quality/audit.py` 记录检索参数（query/日期/来源）保证可复现 | `bioresearch-literature-analysis` |

## 使用约定

- **确定性优先**：所有流程默认使用固定随机种子（`seed=42`），保证可复现。
- **证据分级**：每个流程产出带 `evidence_grade`（A/B=真实公共数据，C=合成/方法学）的 Evidence Package，见 `bio-research-os/eval/`。
- **阴性结果不丢弃**：非显著结果由 `engines/negative_result.py` 显式标注，见该模块。
- **数据治理**：受控访问 / 个体级数据（MetaBrain / UKB-PPP / ADNI / deCODE / 个人基因组）在加载前即被 `quality/governance.py` 拦截，详见 `DATA_GOVERNANCE.md`。

## 新增黄金流程的模板

新增一个黄金流程时，请在 `skills/` 下提供对应 Skill，并在本表补一行，同时确保：

1. 在 `quality/assertions.py` 中声明其不可绕过质控断言（或复用已有断言）；
2. 在 `quality/governance.py` 中确认不触及受控数据；
3. 在 `quality/audit.py` 中记录关键执行参数（保证链式哈希可审计）。
