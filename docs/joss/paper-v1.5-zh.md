---
title: 'BioResearch Agent Framework v1.5：面向真实公开 summary 数据的因果证据链验证'
tags:
  - bioinformatics
  - reproducibility
  - workflow
  - mendelian-randomization
  - colocalization
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

BioResearch Agent Framework 是一个面向生物医学研究的可重复工作流执行层，而非自主科学推理系统。v1.5 的核心升级有两项：一是在仓库层面建立数据治理护栏，明确区分公开 summary 数据与受控/个体级数据；二是将验证套件从 5 个案例扩展到 6 个，并首次在真实公开 summary 数据上运行因果证据链（GWAS → eQTL → colocalization → TWAS → fine-mapping → MR）。

Case 6 采用 Jansen et al. 2019 阿尔茨海默病（AD）GWAS 汇总统计与 GTEx v8 13 个脑区 cis-eQTL，针对 TREM2、BIN1、CLU、PICALM、APOE 五个已知 AD 基因进行验证。5/5 基因成功匹配到脑 eQTL，4/5 基因呈现强共定位信号（PP.H4 > 0.8），BIN1 同时通过 Wald-ratio MR 检验（β = 0.037，SE = 0.006，p = 9.0 × 10⁻¹⁰）。证据等级评定为 B（真实公开 summary 数据），并明确标注了 lead-eQTL-only、无 LD 参考面板等限制。该版本证明框架可在不触碰受控数据的前提下，对真实遗传汇总数据进行可审计的因果证据整合。

**关键词：** 生物信息学；可重复工作流；因果推断；孟德尔随机化；共定位分析；agent skills

# 1. 引言

当前生物医学领域的 AI 助手大多停留在“生成代码或文本”阶段：它们可以写出看似合理的分析脚本，却很难保证脚本真实运行、输出可审计、结果可复现。与此同时，Nextflow、Snakemake 等工作流引擎解决了计算流程的便携执行问题，却未提供面向 AI 助手的标准化调用接口。BioResearch Agent Framework 的定位是填补这一间隙：把经过验证的生物医学工具封装为可执行的工作流，并通过 CLI、Python SDK、API 契约与 Agent Skill 四层接口暴露给研究者或 AI 助手。

v1.0–v1.1 的验证以公开 GEO 数据和合成 GWAS 为主，证据等级最高为 B，但因果推断模块仍依赖合成数据来验证计算正确性。v1.5 的目标是在真实公开 summary 数据上完成因果证据链的端到端验证，并在此过程中建立数据治理边界，确保不会意外引入受控访问或个体级数据。

# 2. 系统定位与数据治理

框架坚持“可重复执行契约”而非“新算法”。所有统计计算都委托给成熟库：差异表达使用 t-test + Benjamini–Hochberg 校正，通路富集使用超几何检验，因果推断使用 inverse-variance weighted MR 与 Wald-ratio MR，因果证据链使用 coloc、TWAS z-score、可信集与 MR。框架本身只负责标准化输入输出、固定种子、记录来源（provenance）和诚实的证据等级。

数据治理政策 `DATA_GOVERNANCE.md` 将数据分为四个层级：

| 层级 | 示例 | 是否可用 | 是否可提交到仓库 |
|:---|:---|:---|:---|
| 公开开放获取 | GEO、GTEx eQTL summary、PubMed、GO/KEGG | 是 | 仅框架自身产生的衍生结果（CSV/图/evidence package） |
| 注册后获取的 summary 数据 | FinnGen、eQTLGen | 是（用户提供本地路径） | 否 |
| 受控访问 / 个体级数据 | MetaBrain、UKB-PPP、ADNI、deCODE | 否 | 否 |
| 其他项目的衍生结果 | 他人的 `processed/`、`figures/` | 否 | 否 |

`.gitignore` 已强化为排除所有原始压缩数据与 `raw/`、`downloads/` 等目录。v1.5 的真实数据验证严格限定在 Jansen 2019 AD GWAS summary 统计与 GTEx v8 脑 eQTL summary 统计，均属于公开 summary 数据，且仅通过本地路径加载，不会进入仓库。

# 3. v1.5 验证套件

验证套件从 5 个案例扩展到 6 个，注册在 `bio-research-os/eval/manifest.json` 中。每个案例都附带 Evidence Package，包含来源、方法、结果、证据等级与限制。

| ID | 名称 | 工作流 | 数据 | 证据等级 |
|:---:|:---|:---|:---|:---:|
| 1 | 帕金森病生物标志物发现 | biomarker-discovery | GEO GSE7621（真实 public microarray） | B |
| 2 | AD 因果推断（风险因素 → AD） | causal-inference | 合成 GWAS + 真实 IVW 引擎 | C |
| 3 | AD 文献空白分析 | literature-analysis | PubMed / 离线内置语料 | B / C |
| 4 | 暴露 → 结局 MR 示例 | causal-inference | 合成 GWAS + 真实 IVW 引擎 | C |
| 5 | 因果证据链（合成位点） | causal-evidence | 合成位点（ground truth 已知） | C |
| 6 | 真实 AD GWAS + GTEx 脑 eQTL 因果证据链 | causal-evidence | Jansen 2019 + GTEx v8（真实 public summary） | B |

套件不是排行榜，而是一组“诚实的可重复性测试”。合成案例（C 级）验证引擎逻辑正确；真实数据案例（B 级）验证引擎在公开数据上的实际可用性。

# 4. 因果证据引擎

因果证据链工作流将 GWAS 与 eQTL 信号整合为四级证据：

1. **共定位（coloc）**：计算 PP.H4，判断 GWAS 与 eQTL 是否共享同一因果变异。
2. **TWAS 代理**：使用 lead eQTL 的 Z 值作为基因表达工具变量代理，计算 TWAS z-score 与 p 值。
3. **精细映射（fine-mapping）**：在每个基因座内构建可信集（credible set），为 MR 提供候选工具变量。
4. **Wald-ratio MR**：以可信集中的 lead eQTL SNP 为工具，估计基因表达对结局的因果效应。

当前实现是 summary-statistics-only 的近似版本：只使用 GTEx 的 lead cis-eQTL，不对 SNP 之间的 LD 建模，也不使用完整 eQTL 权重矩阵。这既是出于数据治理的保守选择，也决定了结果应被解读为“概念验证”而非“最终因果结论”。

# 5. Case 6：真实 AD GWAS + GTEx 脑 eQTL 验证

## 5.1 数据与目标

- **GWAS**：Jansen et al. 2019 AD case/control 汇总统计（hg19），约 960 万 SNP。
- **eQTL**：GTEx v8 13 个脑区 cis-eQTL（hg38），取每个基因在每个组织的 lead eQTL。
- **目标基因**：TREM2、BIN1、CLU、PICALM、APOE，均为已知 AD 风险位点。
- **匹配策略**：按 dbSNP rsID 匹配 GWAS 与 eQTL SNP；无 rsID 或链歧义的 SNP 被丢弃。

## 5.2 主要结果

5/5 目标基因至少匹配到一个脑 eQTL lead SNP；4/5 基因显示强共定位（PP.H4 > 0.8）；1/5 基因通过 MR 显著性检验（p < 0.05）。

| 基因 | 最佳脑区 | PP.H4 | TWAS z | TWAS p | MR β | MR SE | MR p | 可信集大小 |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| BIN1 | Brain_Cerebellum | 0.991 | 0.350 | 0.727 | 0.037 | 0.006 | **9.0 × 10⁻¹⁰** | 10 |
| APOE | Brain_Cerebellar_Hemisphere | 0.995 | −0.445 | 0.656 | 0.0004 | 0.007 | 0.958 | 11 |
| CLU | Brain_Frontal_Cortex_BA9 | 0.984 | −1.414 | 0.157 | −0.010 | 0.016 | 0.550 | 12 |
| PICALM | Brain_Cerebellar_Hemisphere | 0.867 | 1.531 | 0.126 | −0.009 | 0.010 | 0.367 | 10 |
| TREM2 | Brain_Substantia_nigra | 0.123 | 1.281 | 0.200 | 0.030 | 0.037 | 0.425 | 11 |

BIN1 的结果与 AD 遗传学文献一致：该位点的 GWAS 信号与脑 eQTL 信号强共定位，且通过单 SNP MR 检测到基因表达对 AD 风险的正向因果效应。APOE 虽然共定位极强，但 lead-eQTL 模型无法捕捉 ε2/ε3/ε4 拷贝数结构，因此 MR 不显著。TREM2 的共定位信号较弱，可能与其风险效应主要由罕见变异和小胶质细胞特异性调控主导、而 GTEx 以常见变异和混合脑组织为主有关。

## 5.3 证据等级与限制

Case 6 的证据等级为 **B**（真实公开 summary 数据）。主要限制包括：

- 仅使用 lead cis-eQTL，未使用完整 eQTL 权重矩阵；TWAS 为 z-score 代理，效能低于 S-PrediXcan / FUSION。
- 未引入 LD 参考面板，同一基因座内的 SNP 被视作独立。
- Wald-ratio MR 仅使用单 SNP 工具，无法调整水平多效性或 LD。
- GTEx eQTL 来自 mostly non-diseased 脑组织，与 AD case/control GWAS 存在组织-疾病状态差异。

这些限制被完整写入 Evidence Package（`CE_real_evidence_package.json`），并在 `CE_real_summary_report.txt` 中显式列出。

# 6. 合成验证与真实验证的对比

Case 5（合成位点）与 Case 6（真实 AD 数据）的设计差异和结果差异如下：

| 维度 | Case 5（合成） | Case 6（真实 summary） |
|:---|:---|:---|
| 证据等级 | C | B |
| GWAS | 模拟 AD 位点，因果结构已知 | Jansen et al. 2019 真实 AD GWAS |
| eQTL | 模拟 cis-eQTL，效应已知 | GTEx v8 13 个脑区 lead eQTL |
| 基因数 | 8（2 个真实共定位） | 5（TREM2 / BIN1 / CLU / PICALM / APOE） |
| 共定位恢复率 | 2/2 = 100% | 4/5 = 80%（按 PP.H4 > 0.8） |
| TWAS 显著率 | 2/2 = 100% | 0/5 |
| MR 显著率 | 2/2 = 100% | 1/5（BIN1） |
| 精细映射真实因果 SNP 覆盖 | 100% | 无 ground truth，未评估 |

合成数据中的共定位基因共享同一个因果 SNP，且效应被人为放大，因此 PP.H4 = 1.0、TWAS/MR 极显著。真实数据则包含 LD、多因果变异、组织异质性、罕见变异以及 APOE 这类特殊等位基因结构，lead-eQTL-only 模型会丢失部分信号。Case 6 中 TWAS 不显著并不等价于“无生物学意义”，而是反映了当前简化模型的统计效能不足。BIN1 的复现说明，对于最稳健的位点，引擎仍能在真实 summary 数据上捕获强因果证据。

# 7. 讨论

v1.5 的交付物不是新的因果发现，而是证明一个轻量、可审计、agent 可调用的执行层能够在真实公开 summary 数据上跑通因果证据链，并诚实地标注证据等级与限制。这一结果有三层意义：

- **可重复性**：每个案例的 Evidence Package 固定了 git commit、Python 版本、数据来源、SHA256 与参数，使结果可被复核。
- **数据治理**：通过 `DATA_GOVERNANCE.md` 与 `.gitignore`，框架在设计上排除了受控/个体级数据，降低了公开仓库的法律与隐私风险。
- **诚实性**：B 级证据明确区别于 A 级实验验证，也不同于 C 级合成验证；Case 6 的 limitations 段落阻止了过度推断。

当前实现仍有明显近似：lead-eQTL-only 的 TWAS、无 LD 的 coloc、单 SNP MR。下一步应引入 S-PrediXcan / FUSION 的完整 eQTL 权重、1000 Genomes LD 参考面板、以及 coloc.susie 等多因果共定位方法。这些升级依赖的数据（GTEx 权重、1000G LD）仍为公开数据，符合数据治理框架；而 MetaBrain、UKB-PPP 等受控数据将继续被排除。

# 8. 结论

BioResearch Agent Framework v1.5 将框架验证从合成数据推进到真实公开 summary 数据，完成了 6 个验证案例的注册，并在 Jansen 2019 AD GWAS 与 GTEx v8 脑 eQTL 上成功复现了 BIN1 的强共定位与显著 MR 证据。数据治理护栏与 Evidence Package 机制确保了这一过程可审计、可复现、不越界。后续工作将聚焦于引入完整 eQTL 权重与 LD 参考面板，把当前 B 级概念验证推向更可靠的因果证据整合。

# 参考文献

1. Di Tommaso, P., Chatzou, M., Floden, E. W., Barja, P. P., Palumbo, E., & Notredame, C. (2017). Nextflow enables reproducible computational workflows. *Nature Biotechnology*, 35(4), 316–319.
2. Mölder, F., Jablonski, K. P., Letcher, B., Hall, M. B., Tomkins-Tinch, C. H., Sochat, V., … others. (2021). Sustainable data analysis with Snakemake. *F1000Research*, 10, 33.
3. Ritchie, M. E., Phipson, B., Wu, D., Hu, Y., Law, C. W., Shi, W., & Smyth, G. K. (2015). limma powers differential expression analyses for RNA-sequencing and microarray studies. *Nucleic Acids Research*, 43(7), e47.
4. Hemani, G., Zheng, J., Elsworth, B., Wade, K. H., Haberland, V., Baird, D., … others. (2018). The MR-Base platform supports systematic causal inference across the human phenome. *eLife*, 7, e34408.
5. Jansen, I. E., Savage, J. E., Watanabe, K., Bryois, J., Williams, D. M., Steinberg, S., … others. (2019). Genome-wide meta-analysis identifies new loci and functional pathways influencing Alzheimer’s disease risk. *Nature Genetics*, 51(3), 404–413. https://doi.org/10.1038/s41588-018-0311-9
6. GTEx Consortium. (2020). The GTEx Consortium atlas of genetic regulatory effects across human tissues. *Science*, 369(6509), 1318–1330. https://doi.org/10.1126/science.aaz1776
7. Giambartolomei, C., Vukcevic, D., Schadt, E. E., Franke, L., Hingorani, A. D., Wallace, C., & Plagnol, V. (2014). Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. *PLoS Genetics*, 10(5), e1004383. https://doi.org/10.1371/journal.pgen.1004383
8. Gusev, A., Ko, A., Shi, H., Bhatia, G., Chung, W., Penninx, B. W. J. H., … Pasaniuc, B. (2016). Integrative approaches for large-scale transcriptome-wide association studies. *Nature Genetics*, 48(3), 245–252.
