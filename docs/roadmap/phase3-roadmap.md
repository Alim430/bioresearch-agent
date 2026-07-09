# BioResearch Agent Phase 3 路线图

> 版本: v1.6 → Phase 3 规划
> 日期: 2026-07-09
> 状态: 规划中

---

## 1. 总体愿景

Phase 3 的目标是将框架从"单模态因果遗传学 + 单细胞嵌入评估"扩展到"基因 → 细胞状态 → 表型"的完整因果链。三个方向在 AD-VCP（Alzheimer's Disease Virtual Cell Project）愿景下汇合：

```
基因变异 (GWAS) ──→ 基因表达调控 (eQTL/TWAS) ──→ 细胞状态 (Foundation Models) ──→ 表型 (AD)
     │                        │                          │                           │
  跨祖先 MR              因果证据链                 多模态整合                  虚拟细胞
  (Phase 3a)           (v1.5/v1.6 已有)           (Phase 3b)                 (Phase 3c)
```

---

## 2. 方向一：跨祖先孟德尔随机化（Phase 3a）

### 2.1 背景与动机

当前框架的因果推断（Case 2/4/6）均基于欧洲人群 GWAS summary。然而：

- **可迁移性假设不成立**：不同祖先群体的 LD 结构、等位基因频率、基因-环境交互均不同，工具变量不可直接跨群迁移。
- **多样性缺口**：90% 的 GWAS 来自欧洲人群，但疾病风险变异的效应在非欧洲人群中可能不同。
- **多效性结构差异**：跨祖先 MR 需显式建模相关与不相关水平多效性。

### 2.2 技术方案

| 组件 | 方法/工具 | 数据需求 | 计算需求 |
|:---|:---|:---|:---|
| GWAS summary 获取 | Biobank Japan / FinnGen / 台湾 TPMI / PAGE | 公开下载 | CPU |
| LD 参考面板 | 1000 Genomes 各亚群 (AFR/AMR/EAS/SAS) | 公开下载 | CPU |
| 工具变量选择 | 跨祖先 LD clumping + F 统计量 | LD 面板 + GWAS | CPU |
| MR 估计 | IVW / MR-Egger / 加权中位数 | 两样本 GWAS | CPU |
| 多效性建模 | CAUSE (Morrison et al. 2020) / MRMix (Wang et al. 2020) | GWAS summary | CPU |
| 敏感性分析 | MR-PRESSO / MRlap | GWAS summary | CPU |
| 跨祖先 meta | 分层分析后 meta，或跨祖先 meta-GWAS | 多队列 | CPU |

### 2.3 公开数据资源

| 资源 | 人群 | 规模 | 可及性 | 治理合规 |
|:---|:---|:---|:---|:---:|
| Biobank Japan (BBJ) | 日本 | ~20 万, ~220 表型 | PheWeb 公开下载 | ✅ |
| FinnGen | 芬兰 | 数十万 | 汇总统计公开 | ✅ |
| 台湾 TPMI | 汉族 | 56 万, 719 表型 | 公开下载 | ✅ |
| IEU OpenGWAS | 通用 | 海量 | 公开 | ✅ |
| GWAS Catalog / EBI GWAS-SSF | 通用 | 海量 | 公开, 标准化 | ✅ |
| 1000 Genomes | 多祖先 | ~3000 样本 | 公开 | ✅ |
| PAGE Study | 非裔/拉美/亚裔 | ~5 万 | 部分需 dbGaP | ⚠️ 部分 |

### 2.4 新增技能计划

1. **bioresearch-gwas-harmonization**: GWAS 汇总统计获取、格式标准化（GWAS-SSF）、多队列等位基因对齐
2. **bioresearch-ancestry-aware-mr**: 跨祖先 MR 分析（CAUSE/MRMix + 分层 LD clumping + 可移植性评估）
3. **bioresearch-ld-reference-management**: 1000 Genomes 各亚群 LD 参考面板管理

### 2.5 验证案例规划

- **Case 8**: 跨祖先 BMI → T2D MR（BBJ + FinnGen + UKB-PPP summary）
  - 证据等级: B（真实公开 summary 数据）
  - 目标: 验证跨祖先工具变量可移植性与多效性建模
- **Case 9**: 跨祖先 AD MR（Jansen 2019 欧洲队列 + BBJ AD GWAS）
  - 证据等级: B
  - 目标: 验证已知 AD 位点在东亚人群中的因果证据一致性

### 2.6 数据治理评估

**最高契合度**——MR 天然基于公开汇总统计量，不需个体数据，与 "public summary data only" 完美匹配。BBJ、FinnGen、TPMI、IEU OpenGWAS 均为开放下载，1000G LD 参考面板公开。仅需排除需 dbGaP 受控访问的 PAGE 部分。

### 2.7 优先级

**Phase 3 早期突破口**——治理摩擦最小、计算需求最低（CPU only）、可独立快速落地。

---

## 3. 方向二：多模态单细胞整合（Phase 3b）

### 3.1 背景与动机

v1.6 的 foundation embeddings skill 仅处理 RNA-only 数据。多模态单细胞技术（CITE-seq、10x Multiome）已成为细胞状态表征的前沿，且基础模型（scGPT）已向多组学扩展。

### 3.2 技术方案

| 组件 | 方法/工具 | 数据需求 | 计算需求 |
|:---|:---|:---|:---|
| 多模态数据加载 | MuData / AnnData | 公开 CITE-seq/Multiome 数据 | CPU |
| 概率多模态整合 | totalVI (RNA+蛋白) / MultiVI (RNA+ATAC) / MOFA+ | 配对多模态数据 | GPU (推荐) |
| 基础模型嵌入 | scGPT 多组学模式 / Geneformer | 预训练 checkpoint | GPU |
| 模态补全 | MultiVI 跨模态推断 (RNA→ATAC/蛋白) | 配对训练数据 | GPU |
| 空间转录组整合 | Squidpy / Cell2location 去卷积 | 公开 Visium/Slide-seq | GPU |
| 整合质量评估 | scIB 指标 (批次校正 vs 生物保守) | 整合后数据 | CPU |

### 3.3 公开数据资源

| 资源 | 类型 | 规模 | 可及性 |
|:---|:---|:---|:---|
| NeurIPS 2021 CITE-seq/Multiome | 配对多模态 | 沙盒数据集 | 公开 |
| 10x Genomics PBMC Multiome demo | RNA+ATAC | ~10K 细胞 | 公开 |
| CZ CELLxGENE Census | 单细胞图谱 | 5000 万+ 细胞 | CC0 公开 |
| Tabula Sapiens | 跨组织参考 | 110 万细胞 | 公开 |
| DOGMA-seq 公开数据 | 三模态 | ~10K 细胞 | 公开 |

### 3.4 新增技能计划

1. **bioresearch-multimodal-integration**: 多模态单细胞整合（totalVI/MultiVI/MOFA+）
2. **bioresearch-cross-modal-inference**: 模态补全与跨模态推断（RNA→ATAC/蛋白）
3. **bioresearch-spatial-transcriptomics**: 空间转录组整合（从 planned 升级为 active）

### 3.5 验证案例规划

- **Case 10**: NeurIPS 2021 CITE-seq 整合基准
  - 证据等级: C（公开基准数据，方法论验证）
  - 目标: 验证 totalVI 整合管线在已知基准上的表现
- **Case 11**: 10x Multiome PBGC 多模态细胞类型注释
  - 证据等级: B（公开真实数据）
  - 目标: 验证 MultiVI + scGPT 多组学嵌入的细胞类型恢复

### 3.6 与 v1.6 的衔接

直接扩展 v1.6 foundation embeddings skill：
- Mock 模式: 模拟多模态嵌入（RNA dim + ATAC dim + 蛋白 dim）
- Live 模式: scGPT 多组学 API + totalVI/MultiVI 推理
- 评估指标复用: silhouette/ARI/NMI/kNN overlap + 新增跨模态恢复指标

### 3.7 优先级

**Phase 3 中期**——需 GPU 推理基础设施，与 Phase 3c (Virtual Cell) 共享基础模型推理层。

---

## 4. 方向三：Virtual Cell（Phase 3c）

### 4.1 背景与动机

AI Virtual Cell (AIVC) 是 2024 年 Cell 观点文章提出的纲领性概念：一个多尺度、多模态、基于大型神经网络的模型，能表征并模拟细胞在不同状态下的行为。Arc Institute 于 2025 年发起首届 Virtual Cell Challenge，目标是"虚拟细胞的 AlphaFold 时刻"。

### 4.2 核心资源

| 资源 | 描述 | 规模 | 可及性 |
|:---|:---|:---|:---|
| CZ CELLxGENE Census | 标准化单细胞数据集合 | 5000 万+ 细胞 | CC0 公开 |
| Arc Virtual Cell Atlas | 大规模细胞图谱 | 3 亿+ 细胞 | CC0 公开 |
| Tahoe-100M | 癌细胞系 + 药物扰动 | 1 亿细胞, 1100+ 小分子 | CC0 公开 |
| scBaseCount | 多物种细胞计数 | 2 亿+ 细胞, 21 物种 | 公开 |
| H1 hESC CRISPRi 基准 | 扰动响应基准 | 30 万细胞, 300 基因 | 公开 |
| Replogle Perturb-seq | 全基因组扰动 | 250 万细胞, 2500 基因 | 公开 |

### 4.3 技术方案

| 组件 | 方法/工具 | 数据需求 | 计算需求 |
|:---|:---|:---|:---|
| Census 数据切片 | cellxgene-census API (TileDB-SOMA) | CZ CELLxGENE | CPU (大内存) |
| 虚拟细胞模型推理 | TranscriptFormer / scGPT / STATE | 预训练 checkpoint | GPU |
| 扰动响应预测 | GEARS / scGPT perturbation API | 扰动数据 + 基态 | GPU |
| 评测指标 | DES (差异表达匹配) / PDS (扰动区分度) / MAE | 预测 vs 真实 | CPU |
| 细胞类型映射 | CellGuide / Census ontology | Census | CPU |
| 模型-实验闭环 | 预测 → 建议验证实验 → 结果反馈 | 迭代 | 混合 |

### 4.4 新增技能计划

1. **bioresearch-census-query**: CZ CELLxGENE Census 数据切片与查询
2. **bioresearch-virtual-cell-inference**: 虚拟细胞模型加载与推理
3. **bioresearch-perturbation-prediction**: 扰动响应预测（GEARS/scGPT）
4. **bioresearch-cell-state-simulation**: 细胞状态模拟与轨迹预测

### 4.5 验证案例规划

- **Case 12**: H1 hESC CRISPRi 扰动响应预测
  - 证据等级: B（公开基准数据）
  - 目标: 验证扰动预测管线在已知基准上的 DES/PDS 表现
- **Case 13**: AD 小胶质细胞状态模拟
  - 证据等级: C→B（从合成数据迁移到公开 AD 单细胞数据）
  - 目标: 模拟小胶质细胞在 AD 风险基因扰动下的状态转变

### 4.6 数据治理评估

**高契合度**——Census 和 Atlas 均为 CC0 公开数据，核心观测+扰动资源均公开。Agent 可完全基于公开数据推理虚拟细胞模型。唯一限制：少量患者来源单细胞数据受 dbGaP 控制，但非必需。

### 4.7 优先级

**Phase 3 远期**——需最强 GPU 推理能力，但与 Phase 3b 共享基础设施，且是三方向汇合的终点。

---

## 5. 三方向横向对比

| 维度 | 跨祖先 MR (3a) | 多模态整合 (3b) | Virtual Cell (3c) |
|:---|:---|:---|:---|
| 数据治理契合度 | **最高** (纯 summary) | 高 (公开 AnnData) | 高 (CC0 数据) |
| 计算需求 | 低 (CPU) | 高 (GPU) | **最高** (GPU + 大内存) |
| 与 v1.6 衔接 | 需新因果模块 (复用证据链) | 直接扩展 FM embeddings skill | 扩展 FM + 新增 Census 接口 |
| 新增技能数 | 3 | 3 | 4 |
| 新增验证案例 | 2 (Case 8-9) | 2 (Case 10-11) | 2 (Case 12-13) |
| 预计 Benchmark 任务 | +2 (Group H) | +2 (Group I) | +2 (Group J) |
| 与 AD-VCP 汇合点 | 因果推断 | 细胞状态表征 | 扰动预测 |
| 实施优先级 | **1** (快速落地) | **2** (需 GPU) | **3** (需最强 GPU) |

---

## 6. 实施时间线

### Phase 3a: 跨祖先 MR（预计 2-3 周）

1. Week 1: GWAS harmonization skill + LD 参考面板管理 skill
2. Week 2: 跨祖先 MR skill (CAUSE/MRMix) + Case 8/9 实现
3. Week 3: Benchmark-Lite Group H + manuscript 更新 + git push

### Phase 3b: 多模态单细胞整合（预计 3-4 周）

1. Week 1: 多模态数据加载 + totalVI/MultiVI 整合 skill
2. Week 2: 跨模态推断 + 空间转录组 skill
3. Week 3: Case 10/11 实现 + scGPT 多组学 live mode
4. Week 4: Benchmark-Lite Group I + manuscript 更新

### Phase 3c: Virtual Cell（预计 4-6 周）

1. Week 1-2: Census 查询 skill + 数据切片管线
2. Week 3-4: 虚拟细胞模型推理 skill + 扰动预测 skill
3. Week 5: Case 12/13 实现 + 评测指标 (DES/PDS/MAE)
4. Week 6: Benchmark-Lite Group J + 三方向整合 manuscript

---

## 7. 框架版本规划

| 版本 | Phase | 新增内容 | Active Skills | Cases | Benchmark Tasks |
|:---|:---|:---|:---:|:---:|:---:|
| v1.6.0 (当前) | Phase 2 mock | Foundation embeddings (mock) | 11 | 7 | 21 |
| v1.7.0 | Phase 2 live | Foundation embeddings (live) | 11 | 7 | 21 |
| v1.8.0 | Phase 3a | 跨祖先 MR | 14 | 9 | 23 |
| v1.9.0 | Phase 3b | 多模态整合 | 17 | 11 | 25 |
| v2.0.0 | Phase 3c | Virtual Cell | 21 | 13 | 27 |

---

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|:---|:---|:---|:---|
| GPU 资源不足 | 中 | 高 (Phase 3b/3c 受阻) | 优先 CPU-only 的 Phase 3a; 使用 Colab/云 GPU 按需 |
| 模型 checkpoint 版本变化 | 低 | 中 | 固定 checkpoint 版本 + SHA256 记录 |
| Census API 不稳定 | 低 | 中 | 本地缓存 + 离线 fallback |
| 跨祖先 LD 面板不完整 | 中 | 中 | 使用 1000G 各亚群 + UKB-PPP summary (如可用) |
| 多模态数据格式不统一 | 中 | 低 | 依赖 MuData/AnnData 标准 + scvi-tools 兼容 |

---

## 9. 参考文献

1. Bunne, Y., et al. (2024). How to build the virtual cell with artificial intelligence: Priorities and opportunities. *Cell*, 187(25), 7045–7063.
2. Cui, H., et al. (2024). scGPT: Toward building a foundation model for single-cell multi-omics using generative pretraining. *Nature Methods*, 21, 1470–1480.
3. Hao, M., et al. (2024). Large-scale foundation model on single-cell transcriptomics. *Nature Methods*, 21, 1481–1491.
4. Rosen, Y., et al. (2024). Universal cell embeddings: A foundation model for cell biology. *bioRxiv*.
5. Morrison, J., et al. (2020). Mendelian randomization accounting for correlated and uncorrelated pleiotropic effects using genome-wide summary statistics. *Nature Genetics*, 52, 740–747.
6. Wang, J., et al. (2020). MRMix: A robust statistical method for Mendelian randomization analysis accounting for correlated and uncorrelated pleiotropy. *American Journal of Human Genetics*, 107(4), 728–742.
7. Gayoso, A., et al. (2021). Joint probabilistic modeling of single-cell multi-omic data with totalVI. *Nature Methods*, 18, 272–282.
8. Ashuach, T., et al. (2023). MultiVI: Deep generative model for the integration of multi-modal data. *Nature Methods*, 20, 1220–1231.
9. Argelaguet, R., et al. (2020). MOFA+: a statistical framework for comprehensive integration of multi-modal single-cell data. *Genome Biology*, 21, 111.
10. Lopez, R., et al. (2018). Deep generative modeling for single-cell transcriptomics. *Nature Methods*, 15, 1053–1058.
11. Gayoso, A., et al. (2022). scvi-tools: a library for probabilistic analysis of single-cell omics data. *Nature Biotechnology*, 40, 640–650.
12. Replogle, J. M., et al. (2022). Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. *Cell*, 185(14), 2559–2575.
13. Luecken, M. D., et al. (2022). Benchmarking atlas-level data integration in single-cell genomics. *Nature Methods*, 19, 41–50.
14. Hao, Y., et al. (2021). Integrated analysis of multimodal single-cell data. *Cell*, 184(13), 3573–3587.
15. Cao, Z., & Gao, G. (2022). Multi-omics single-cell data integration and regulatory inference with graph-linked embedding. *Nature Biotechnology*, 40, 1458–1466.
