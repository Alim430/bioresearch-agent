# Case 5 vs Case 6：合成验证与真实数据验证的差异分析

## 1. 设计差异

| 维度 | Case 5（合成） | Case 6（真实公开 summary） |
|---|---|---|
| **证据等级** | C | B |
| **GWAS** | 模拟 AD 位点，效应已知 | Jansen et al. 2019 AD GWAS 汇总统计 |
| **eQTL** | 模拟 cis-eQTL，效应已知 | GTEx v8 13 个脑区 cis-eQTL lead SNP |
| **基因** | 8 个合成基因（2 colocalized） | 5 个已知 AD 基因（TREM2/BIN1/CLU/PICALM/APOE） |
| **目标** | 验证 causal-evidence 引擎能恢复 ground truth | 验证引擎在真实公开 summary 数据上能复现已知 AD 基因 |

## 2. 核心结果对比

| 指标 | Case 5 | Case 6 |
|---|---|---|
| 基因匹配率 | 8/8 | 5/5 |
| Colocalization（PP.H4 > 0.8） | 2/2 真实 colocalized 基因 = 100% | 4/5（BIN1/CLU/PICALM/APOE） |
| TWAS 显著 | 2/2 colocalized 基因（p < 1e-140） | 0/5（均不显著，p > 0.05） |
| MR 显著 | 2/2 colocalized 基因（p ~1e-62） | 1/5（BIN1，p = 9e-10） |
| Fine-map 可信集覆盖 | 100% | 未评估真实因果 SNP（无 ground truth） |

## 3. 逐基因解读

| 基因 | Case 6 PP.H4 | Case 6 TWAS p | Case 6 MR p | 生物学含义 |
|---|---|---|---|---|
| BIN1 | 0.991 | 0.727 | **9.0e-10** | 强共定位 + 显著 MR，与 AD 风险因果关联证据最强 |
| APOE | 0.995 | 0.656 | 0.958 | 强共定位，但单 lead eQTL 无法捕捉 APOE ε2/ε3/ε4 拷贝数效应；MR 不显著 |
| CLU | 0.984 | 0.157 | 0.550 | 强共定位，但 TWAS/MR 不显著 |
| PICALM | 0.867 | 0.126 | 0.367 | 共定位证据中等，TWAS/MR 不显著 |
| TREM2 | 0.123 | 0.200 | 0.425 | 低共定位；可能原因：TREM2 罕见变异效应强、lead eQTL 无法代表小胶质细胞特异性调控、GTEx 脑组织非疾病状态 |

## 4. 关键差异原因

1. **合成数据过强**：Case 5 中 colocalized 基因的 GWAS 与 eQTL 共享同一个因果 SNP，且效应被故意设得很大，因此 PP.H4=1.0、TWAS/MR 极显著。
2. **真实数据更复杂**：真实 AD 位点多存在 LD、多因果变异、组织异质性、罕见变异、以及 APOE 这种特殊等位基因结构，lead-eQTL-only 的 summary 统计会丢失信号。
3. **TWAS 不显著≠无生物学意义**：Case 6 使用 lead eQTL Z 值做代理 TWAS，没有完整 eQTL 权重矩阵，因此统计效能远低于 S-PrediXcan/FUSION。
4. **BIN1 的复现**：BIN1 在真实数据上同时呈现强共定位（PP.H4=0.991）和显著 MR（p=9e-10），说明 causal-evidence 引擎在真实数据上能捕获最稳健的位点。

## 5. 方法论启示

- Case 5 证明引擎逻辑正确（能识别共定位 + 推断因果）。
- Case 6 证明引擎在真实 summary 数据上有实用价值，但当前简化模型（lead eQTL only、无 LD）会低估真实信号的复杂性。
- 下一步升级方向：引入完整 eQTL 权重（S-PrediXcan/FUSION）、LD-clumped coloc（coloc.susie）、以及 1000G LD 参考 panel。
