---
title: 'BioResearch Agent Framework v1.6：基础模型嵌入与 Mock-to-Live 评估管线'
tags:
  - bioinformatics
  - reproducibility
  - workflow
  - single-cell
  - foundation-models
  - agent-skills
authors:
  - name: Alimujiang Tudiyusufu
    affiliation: "1, 2"
    orcid: ""
affiliations:
  - name: Shanghai University of Traditional Chinese Medicine
    index: 1
  - name: Institute of Basic Medical Sciences, Peking Union Medical College
    index: 2
date: 9 July 2026
---

# 摘要

BioResearch Agent Framework 是一个面向生物医学研究的可重复工作流执行层。v1.6 在 v1.5 因果证据链与数据治理护栏的基础上，引入了第 11 个 active skill——基础模型嵌入（foundation model embeddings），通过 Mock-to-Live 架构验证了 scGPT、UCE、scFoundation 三个单细胞基础模型的评估管线。

Mock 模式利用模拟嵌入（cluster centroids + Gaussian noise + L2 normalization）匹配各模型的输出维度（512/1280/512），验证了完整的评估管线：silhouette score、adjusted Rand index (ARI)、normalized mutual information (NMI)、k-means++ 聚类、kNN 跨模型一致性分析、以及 6 级噪声鲁棒性扫描。验证套件从 6 个案例扩展到 7 个，Benchmark-Lite 从 20 个任务扩展到 21 个，21/21 全部通过。Case 7 的证据等级评定为 B（mock 模式验证管线正确性；真实模型推理需 GPU + checkpoint）。

**关键词：** 单细胞基础模型；scGPT；UCE；scFoundation；可重复工作流；agent skills；Mock-to-Live 架构

# 1. 引言

v1.5 完成了因果证据链在真实公开 summary 数据上的验证（Case 6），并建立了数据治理护栏。然而，框架在单细胞领域仅有文献与生物标志物工作流，缺乏对近年来快速兴起的单细胞基础模型（single-cell foundation models）的支持。

2023–2024 年间，多个单细胞基础模型相继发表：scGPT（Cui et al. 2024, *Nature Methods*）在 3300 万细胞上预训练，支持细胞类型注释、扰动响应预测与多组学整合；UCE（Rosen et al. 2024）通过跨物种训练生成通用细胞嵌入；scFoundation（Hao et al. 2024, *Nature Methods*）以 1 亿参数对 2 万基因同时建模。这些模型的出现使得"以预训练嵌入表征细胞状态"成为单细胞分析的新范式。

v1.6 的目标是将这一范式纳入框架的技能层，同时遵循 Mock-to-Live 原则：先以 mock 模式验证评估管线的正确性，再在具备 GPU 资源时切换至 live 模式加载真实模型 checkpoint。这一策略使框架在无 GPU 环境下仍可运行完整的评估流程，保证了可重复性与 CI 兼容性。

# 2. v1.6 验证套件

验证套件从 6 个案例扩展到 7 个，注册在 `bio-research-os/eval/manifest.json` 中。

| ID | 名称 | 工作流 | 数据 | 证据等级 |
|:---:|:---|:---|:---|:---:|
| 1 | 帕金森病生物标志物发现 | biomarker-discovery | GEO GSE7621（真实 public microarray） | B |
| 2 | AD 因果推断（风险因素 → AD） | causal-inference | 合成 GWAS + 真实 IVW 引擎 | C |
| 3 | AD 文献空白分析 | literature-analysis | PubMed / 离线内置语料 | B / C |
| 4 | 暴露 → 结局 MR 示例 | causal-inference | 合成 GWAS + 真实 IVW 引擎 | C |
| 5 | 因果证据链（合成位点） | causal-evidence | 合成位点（ground truth 已知） | C |
| 6 | 真实 AD GWAS + GTEx 脑 eQTL 因果证据链 | causal-evidence | Jansen 2019 + GTEx v8（真实 public summary） | B |
| **7** | **基础模型嵌入管线验证** | **foundation-embeddings** | **合成单细胞数据（1000 cells × 2000 genes）** | **B** |

Case 7 是 v1.6 的新增案例，使用合成单细胞数据验证基础模型嵌入评估管线。

# 3. 基础模型嵌入技能

## 3.1 Mock-to-Live 架构

框架对每个基础模型采用统一的 Mock-to-Live 架构：

| 模式 | 嵌入生成 | 计算需求 | 用途 |
|:---|:---|:---|:---|
| Mock | 模拟嵌入：cluster centroids + Gaussian noise + L2 normalization | CPU only | 验证评估管线正确性、CI 兼容、无依赖运行 |
| Live | 真实模型推理（API stub） | GPU + checkpoint | 真实模型基准评测 |

三个基础模型的规格定义如下：

| 模型 | 输出维度 | 预训练数据 | 原始论文 | 部署方式 |
|:---|:---:|:---|:---|:---|
| scGPT | 512 | 3300 万细胞 | Cui et al. 2024, *Nat Methods* | `pip install scgpt` (CPU-compatible) |
| UCE | 1280 | 跨物种 36M 细胞 | Rosen et al. 2024 | git clone + GPU |
| scFoundation | 512 | 5000 万细胞 | Hao et al. 2024, *Nat Methods* | git clone + GPU |

## 3.2 自定义评估指标

为避免 sklearn 依赖，框架自行实现了以下核心指标：

- **Silhouette score**：衡量聚类紧密度与分离度，范围 [−1, 1]。
- **k-means++ 聚类**：改进的初始化策略，通过 k 次概率采样选择初始中心。
- **Adjusted Rand Index (ARI)**：纠正随机聚类后的兰德指数，范围 [0, 1]（1 = 完美匹配）。
- **Normalized Mutual Information (NMI)**：归一化互信息，衡量聚类与真实标签的一致性，范围 [0, 1]。

所有指标实现均为纯 NumPy，无 sklearn / scipy 依赖，保证了在最小化环境中即可运行。

## 3.3 跨模型一致性分析

跨模型一致性通过 kNN overlap 量化：对每个细胞，计算其在各模型嵌入空间中的 k 近邻（k=10），然后比较不同模型近邻集的 Jaccard overlap。低 overlap 预期来自不同模型的维度差异和噪声特征。

## 3.4 鲁棒性扫描

对每个模型在 6 个噪声水平 [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] 下重复评估，观察 silhouette、ARI、NMI 随噪声增加的衰减趋势，验证评估管线的稳定性。

# 4. Case 7：基础模型嵌入管线验证

## 4.1 数据与设置

- **合成数据**：1000 cells × 2000 genes，5 种细胞类型，2 个批次。细胞类型通过 cluster centroids 植入，批次效应为线性偏移。
- **Mock 嵌入**：各模型按其输出维度（scGPT 512, UCE 1280, scFoundation 512）生成模拟嵌入。
- **评估**：silhouette / ARI / NMI（ground truth = 5 种细胞类型）、kNN overlap、6 级噪声扫描。
- **随机种子**：seed=42，结果确定性可复现。

## 4.2 主要结果

| 模型 | Silhouette | ARI | NMI |
|:---|---:|---:|---:|
| scGPT | 0.847 | 1.000 | 1.000 |
| UCE | 0.883 | 0.780 | 0.910 |
| scFoundation | 0.810 | 1.000 | 1.000 |

跨模型 kNN overlap：0.09–0.10（低 overlap 符合预期——不同维度和噪声特征模拟了模型特异性的嵌入几何）。

## 4.3 证据等级与限制

Case 7 的证据等级为 **B**（mock 模式验证管线正确性）。主要限制：

- Mock 嵌入为模拟数据，不代表真实模型的嵌入质量。
- ARI = 1.000 反映的是 mock 嵌入对 ground truth 的完美恢复，而非真实模型的聚类能力。
- 真实模型推理需 GPU + checkpoint（scGPT via pip, UCE/scFoundation via git clone）。
- kNN overlap 低值在 mock 模式下由维度差异和噪声模式决定，真实模型的一致性可能不同。

这些限制已在 SKILL.md 的 live mode 部署指南中明确记录，并在 `fe_evidence_package.json` 中完整标注。

# 5. v1.5 回顾：因果证据链

v1.5 的核心成果在 v1.6 中完整保留：

- **数据治理护栏**（`DATA_GOVERNANCE.md` + `.gitignore`）：区分公开 summary 数据与受控/个体级数据。
- **Case 6**（真实 AD GWAS + GTEx 脑 eQTL）：5/5 基因匹配，4/5 强共定位（PP.H4 > 0.8），BIN1 通过 Wald-ratio MR（p = 9.0 × 10⁻¹⁰），证据等级 B。
- **诚实证据分级**：每个案例标注 evidence grade (A–E) 与 limitations。

详见 `docs/case-study/CE_Case5_vs_Case6_comparison.md`。

# 6. Benchmark-Lite 回归测试

Benchmark-Lite 从 20 个任务扩展到 21 个，覆盖七个领域：

| 组 | 任务数 | 覆盖范围 |
|:---|:---:|:---|
| A. Router | 8 | 意图分类与命令映射 |
| B. Core State | 3 | Stage, EvidenceGrade, ResearchState |
| C. Engines | 6 | 六个 Layer-2 引擎隔离测试 |
| D. Pipeline | 1 | 全链路 IDEATION → PUBLICATION |
| E. Registry | 1 | skills/registry.json 结构完整性（11 skills） |
| F. Manifest+Gov | 1 | eval/manifest.json + .gitignore（7 cases） |
| **G. Foundation** | **1** | **foundation-embeddings mock 管线验证** |

全部 21/21 通过，无需网络、无需 pytest、无需 GPU。

# 7. 技能注册表

框架从 10 个 active skills 扩展到 11 个：

| 技能 | 组 | 能力 |
|:---|:---|:---|
| bioresearch-introduction | core | 框架概览与能力图 |
| bioresearch-environment-check | core | 环境与可重复性验证 |
| bioresearch-literature-analysis | biomedical | 文献综述 + 共现知识图谱 |
| bioresearch-biomarker-discovery | biomedical | 生物标志物发现 |
| bioresearch-differential-expression | biomedical | 差异表达分析 |
| bioresearch-pathway-enrichment | biomedical | 通路富集分析 |
| bioresearch-causal-inference | biomedical | 两样本孟德尔随机化 |
| bioresearch-disease-case-study | biomedical | 真实数据疾病案例研究 |
| bioresearch-causal-evidence | biomedical | 因果证据链 |
| bioresearch-agent-router | core | 规则化意图分类 → 工作流 |
| **bioresearch-foundation-embeddings** | **biomedical** | **单细胞基础模型嵌入（scGPT/UCE/scFoundation）** |

# 8. 讨论

v1.6 的交付物不是新的生物学发现，而是一个经过验证的基础模型嵌入评估管线。Mock-to-Live 架构的意义在于：

- **可重复性**：Mock 模式使评估管线在无 GPU、无 checkpoint 的环境下可运行，保证了 CI 兼容和审稿可复核。
- **架构就绪**：Live mode 的 API stub 已在 SKILL.md 中文档化，切换至真实推理只需替换 mock 函数为 API 调用，无需重构评估逻辑。
- **指标独立性**：自定义 silhouette / ARI / NMI / k-means++ 实现避免了 sklearn 依赖，使框架在最小化环境中即可运行。

当前限制在于 mock 嵌入不能反映真实模型的嵌入质量。Live mode 部署需要：(1) scGPT 通过 `pip install scgpt` 安装，CPU 即可推理；(2) UCE / scFoundation 需 git clone 模型仓库 + GPU 推理 + 基因对齐。这些升级不改变评估管线结构，仅替换嵌入生成方式。

# 9. 路线图

- **v1.6 Phase 2（mock mode）**——已完成：管线架构、评估指标、跨模型比较、鲁棒性扫描全部验证。
- **v1.6 Phase 2（live mode）**——下一步：部署真实模型推理，生成真实嵌入基准。
- **Phase 3**——三个方向汇合：
  - **跨祖先 MR**：引入 Biobank Japan / FinnGen / 台湾 TPMI 等非欧洲人群 GWAS summary，配合 1000 Genomes 分层 LD 参考面板，使用 CAUSE / MRMix 显式建模跨祖先多效性。治理摩擦最小（纯 summary 统计）。
  - **多模态单细胞整合**：在 v1.6 foundation embeddings 基础上扩展至 CITE-seq / 10x Multiome，引入 totalVI / MultiVI / MOFA+ 概率整合工具。
  - **Virtual Cell**：对接 CZ CELLxGENE Census（5000 万+ 细胞）与 Arc Virtual Cell Atlas，实现扰动响应预测与细胞状态模拟。

三方向在"基因 → 细胞状态 → 表型"因果链上汇合，与 AD-VCP（Alzheimer's Disease Virtual Cell Project）的愿景一致。

# 10. 结论

BioResearch Agent Framework v1.6 将框架能力从因果遗传学扩展到单细胞基础模型领域，通过 Mock-to-Live 架构在不依赖 GPU 的前提下验证了完整的嵌入评估管线。7 个验证案例、21 个 benchmark 任务、11 个 active skills 共同构成了一个可审计、可复现、agent 可调用的生物医学工作流执行层。后续工作将聚焦于 live mode 部署与 Phase 3 三方向的推进。

# 参考文献

1. Di Tommaso, P., et al. (2017). Nextflow enables reproducible computational workflows. *Nature Biotechnology*, 35(4), 316–319.
2. Mölder, F., et al. (2021). Sustainable data analysis with Snakemake. *F1000Research*, 10, 33.
3. Ritchie, M. E., et al. (2015). limma powers differential expression analyses for RNA-sequencing and microarray studies. *Nucleic Acids Research*, 43(7), e47.
4. Hemani, G., et al. (2018). The MR-Base platform supports systematic causal inference across the human phenome. *eLife*, 7, e34408.
5. Jansen, I. E., et al. (2019). Genome-wide meta-analysis identifies new loci and functional pathways influencing Alzheimer's disease risk. *Nature Genetics*, 51(3), 404–413.
6. GTEx Consortium. (2020). The GTEx Consortium atlas of genetic regulatory effects across human tissues. *Science*, 369(6509), 1318–1330.
7. Giambartolomei, C., et al. (2014). Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*, 10(5), e1004383.
8. Gusev, A., et al. (2016). Integrative approaches for large-scale transcriptome-wide association studies. *Nature Genetics*, 48(3), 245–252.
9. Cui, H., et al. (2024). scGPT: Toward building a foundation model for single-cell multi-omics using generative pretraining. *Nature Methods*, 21, 1470–1480.
10. Rosen, Y., et al. (2024). Universal cell embeddings: A foundation model for cell biology. *bioRxiv*. doi:10.1101/2023.11.28.568918
11. Hao, M., et al. (2024). Large-scale foundation model on single-cell transcriptomics. *Nature Methods*, 21, 1481–1491.
12. Bunne, Y., et al. (2024). How to build the virtual cell with artificial intelligence: Priorities and opportunities. *Cell*, 187(25), 7045–7063.
13. Lopez, R., et al. (2018). Deep generative modeling for single-cell transcriptomics. *Nature Methods*, 15, 1053–1058.
14. Gayoso, A., et al. (2022). scvi-tools: a library for probabilistic analysis of single-cell omics data. *Nature Biotechnology*, 40, 640–650.
15. Morrison, J., et al. (2020). Mendelian randomization accounting for correlated and uncorrelated pleiotropic effects using genome-wide summary statistics. *Nature Genetics*, 52, 740–747.
