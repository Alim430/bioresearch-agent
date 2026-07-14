# BioResearch Agent 公开框架 — 最终升级方案与任务清单（v3 修正版）

> **文档定位**：本文件是 v3 讨论的**收口文档**，替代 Kimi 在 `BioResearch_Agent_v3_Repo_Specific_Upgrade.md` 中提出的"自主 AI 科学家"方案。
> 所有结论均基于**实测仓库状态**（非声称），并严格对齐已锁定的 GitHub 定位红线。
> **最后更新**：2026-07-14

---

## 0. 必读红线（不可擅自修改）

| 红线 | 来源 | 含义 |
|------|------|------|
| 🔴 绝不写 `autonomous agent` / `AI scientist` / `AGI` | 项目 memory（长期锁定） | 公开框架是**可复现工作流框架 + agent 可调用的 skill 接口**，不是会自主思考的科学家 |
| 🔴 B1 闭环发现引擎暂缓 | v1.5 五维评审 | "discovers hypotheses autonomously" 属 hype 风险，非当前交付 |
| 🔴 无私钥入公共仓 | 安全 + 定位 | 禁止在 CI / 公开仓库写入 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 或自动建 PR 改写框架自身 |
| 🔴 无虚构投稿信息 | 锁定策略 | `bioRxiv/`、`arxiv-abstract.md`、`docs/publication/`、`framework/`、`docs/roadmap/`、`docs/joss/paper.md` 一律 gitignore，不进仓库 |
| 🔴 诚实证据分级 | v7 角色 | A/B = 真实公共数据；C = 合成/离线方法学。不得把关联说成因果，不得编造 DOI/PMID |

---

## 1. 决策回顾：从 v3 方案到合规子集

### 1.1 Kimi v3 方案的两大问题

1. **虚构交付（已核实）**
   Kimi 声称交付了 `core/scorer/`、`quality/`、`engine/hmm.py`、`harness_memory/` 等 **18 文件 / 111,550 字符 / 3,268 行**。经 Glob 实测，`github/` 下**这些路径全部不存在**。真实仓库仍是 v1.8/v1.9 结构（`bio-research-os/engines/`、`bioresearch/`、`skills/`、`tests/`、`setup.py`）。因此"完善 v3"实际是**从零写**，而非修补已交付代码。

2. **定位冲突（已识别）**
   v3 方案自称"从科研工具集到 **PI 级 AI 科研 Harness 引擎**"，核心模块是：
   - Meta-Harness 自我进化（CI 里塞 LLM key 并自动建 PR 改写框架）
   - PI 决策引擎（自主判断"值不值得做"）
   - Sub-Agent Spawner（并行自主子 Agent）
   - Cross-Model Router（多 LLM 共识）
   
   这正是典型的**自主 AI 科学家**，直接踩中第 0 节三条红线。附录 D.1 的 `harness-evolution.yml` 还会把 `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` 塞进公共仓 CI 并自动改写框架代码——既违反定位，又是密钥泄露风险。

### 1.2 用户已决决策（按时间线）

| 节点 | 决策 |
|------|------|
| 用户前提 | VCIS 是 AD-VCP 个人项目的私有评分体系，从公开框架核心移除，只保留通用 `EvidenceScorer` 插件接口 |
| 助手核实 | Kimi 18 文件 0 落地；v3 自主层违反红线 → 提出合规子集 |
| 用户选择 | **合规子集 B+C**：只做 `EvidenceScorer` 接口 + 硬性质控断言 + 数据治理拦截 + 审计追踪（无自主推理） |
| 助手执行 | 真实写出 8 个文件并**跑通冒烟测试**（非声称），见第 2 节 |
| **最新澄清（本次）** | VCIS 是另一个具体项目（AD-VCP）的评分系统；**公开仓库不应包含个人研究数据**；最多一套**单独 demo 数据**；**不得使用用于发表的数据** |

### 1.3 VCIS 边界（最新澄清的落地）

- **VCIS 本质**：AD-VCP 项目私有的候选基因评分体系（含 PCM 六维度人群约束、CAH 约束理论层）。
- **公开仓库策略**：
  - ✅ 保留通用 `EvidenceScorer` 抽象接口（与 VCIS 解耦）。
  - ✅ 可附带一个**纯合成 demo Scorer**（用 fake 证据层演示插件怎么接），**零真实 AD-VCP 数据、零发表级数据**。
  - ❌ **绝不**把 VCIS 内部逻辑、PCM/CAH 模块、或任何 AD-VCP 真实候选基因评分结果放进公开仓库。
  - 🔒 VCIS 完整实现只在 `ad-vcp-private/` 私有仓，作为 `VCISScorer(EvidenceScorer)` 接入。

---

## 2. 当前真实交付状态（实测，非声称）

### 2.1 ✅ 已完成 — B+C 真实代码（已 import + 运行验证）

| 包 | 文件 | 内容 | 验证 |
|----|------|------|------|
| `bioresearch/scorer/` | `base.py` | `EvidenceScorer` ABC + `EvidenceLayer`/`ScoredGene`/`LayerConfidence` 数据类 | ✓ 可 import |
| | `default.py` | `DefaultMultiModalScorer`：加权几何均值 + Bootstrap 95% CI + 排名稳定性，`seed=42` | ✓ TREM2 评分确定性复现 |
| | `registry.py` | `PluginRegistry` 内存注册表（VCIS 未来接此接口） | ✓ 注册/查询正常 |
| | `__init__.py` | 导出 + 显式"无自主推理"定位声明 | ✓ |
| `bioresearch/quality/` | `assertions.py` | 8 条硬编码断言（弱 IV F<10 拒绝、Egger 截距、coloc H4、RNA-seq 比对率、scRNA UMI 等）+ `AssertionBatch` + `HardStopException` | ✓ REJECT 真能终止 |
| | `governance.py` | 数据治理拦截器，黑名单 `metabrain/ukb-ppp/adni/decode/personal_genome`，对齐 `DATA_GOVERNANCE.md` | ✓ ADNI/UKB-PPP/MetaBrain 全拦截 |
| | `audit.py` | `AuditTrail` JSONL 链式哈希（跨会话续链，防篡改） | ✓ chain 连续 |
| | `__init__.py` | 导出 | ✓ |

**冒烟测试结果（真实运行输出）**：
```
✓ B.score TREM2 total=0.6657 ci=(0.5621,0.7791) stab=0.7524
✓ B.determinism seed=42 reproducible
✓ C.assertions REJECT triggered: mr_weak_iv
✓ C.governance blocked ADNI/UKB-PPP/MetaBrain/deCODE/personal_genome；放行 IEU OpenGWAS
✓ C.audit chain OK（prev_hash→chain_hash 连续）
```

### 2.2 ✅ 已完成 — 仓库治理 / paper（前期轮次）

- GitHub 清理 intact：`git check-ignore` 确认 0 个 `bioRxiv/` 入库，131 tracked 文件，README 已合规（cs.SE 定位、无 overclaim）。
- `CONTRIBUTING.md` 新增（明确 scope = 可复现工作流框架 + agent skill 接口，非 autonomous）。
- `docs/joss/literature_review.md`：真实文献综述，每条带验证 PMID/DOI。
- `docs/joss/paper-v1.9-draft-en.md`：重组稿（独立 §3 Related Work、修正 MR-Base 误引、补 Snakemake/nf-core/Wilson、新增 §12 Limitations & 诚实分级）。

### 2.3 ❌ Kimi 声称但不存在的（明确标注虚构，不采用）

以下模块在 Kimi 的交付总结里出现，但**磁盘上不存在，且因定位冲突不实现**：
- `engine/hmm.py`（Meta-Harness 自进化状态机）
- `engine/pi_engine.py`（自主 PI 决策引擎）
- `engine/sas.py`（Sub-Agent 并行集群）
- `engine/cmr.py`（跨模型共识路由）
- `BioResearch_Agent_v3_Architecture.md` / `BioResearch_Agent_v3_Final_Delivery.md`（含自主层架构，不采用）
- `harness-evolution.yml`（CI 塞 LLM key + 自动 PR，**安全违规**）

---

## 3. 最终锁定架构

### 3.1 公开框架范围（`bioresearch/` 包）

```
bioresearch-agent/                        # 公开框架（本仓库）
├── bioresearch/
│   ├── scorer/                           # ✅ B 已交付
│   │   ├── base.py                       #   EvidenceScorer ABC + 数据类
│   │   ├── default.py                    #   DefaultMultiModalScorer
│   │   ├── registry.py                   #   PluginRegistry
│   │   └── __init__.py
│   ├── quality/                          # ✅ C 已交付
│   │   ├── assertions.py                 #   硬统计断言 + HardStopException
│   │   ├── governance.py                 #   数据治理拦截（对齐 DATA_GOVERNANCE）
│   │   ├── audit.py                      #   链式哈希审计
│   │   └── __init__.py
│   ├── engines/                          # 既有确定性引擎（非自主）
│   └── ...
├── demo_plugins/                         # 🆕 T1.3：纯合成 demo Scorer（fake 数据，演示接口）
│   └── trivial_scorer.py                 #   不含任何 VCIS / AD-VCP 真实数据
├── skills/                               # 既有 14 个 agent 接口 SKILL.md
├── tests/                                # 🆕 T1.1：pytest 套件
├── setup.py / pyproject.toml             # 🆕 T1.2：entry_points 插件注册
└── README.md                             # 🆕 T1.4：scorer 接口 + 质控文档
```

### 3.2 VCIS 私有边界（`ad-vcp-private/`，不公开）

```
ad-vcp-private/                           # 你的私有项目（不进本仓库）
├── plugins/vcis/
│   ├── vcis_scorer.py                    # VCISScorer(EvidenceScorer) 实现
│   ├── population_constraint.py          # PCM 六维度
│   ├── constraint_theory.py              # CAH 理论层
│   └── benchmark.py                      # PR 曲线 / Top-k（真实 AD-VCP 数据）
```

### 3.3 🚫 明确不做（含理由）

| 模块 | 不做的理由 |
|------|-----------|
| Meta-Harness 自进化 | 违反"非 autonomous"红线；CI 塞 LLM key + 自动 PR 改写框架 = 安全违规 |
| PI 决策引擎（自主 LLM 评判） | 违反"非 autonomous"；"与人工 PI 一致性 >0.7"是不可验证 overclaim |
| SAS 子 Agent 并行集群 | 本质自主多智能体，违反定位 |
| CMR 跨模型共识路由 | 需多 LLM 调用，超出"可复现工作流框架"scope，且引入密钥/成本 |
| 自动写顶刊论文 | 违反诚实/no-overclaim 纪律；"抢占创新高地"话术违规 |
| 把 VCIS 进公开仓 | 用户最新澄清：公开仓不含个人研究数据，最多 demo |

---

## 4. 最终任务清单（按阶段，含验收标准 / 优先级 / 阻塞）

### Phase 0 — 已完成（真实，已验证）

| ID | 任务 | 交付物 | 状态 | 验收 |
|----|------|--------|------|------|
| T0.1 | 证据评分接口包 | `scorer/` 4 文件 | ✅ | import + TREM2 评分确定性复现 |
| T0.2 | 硬性质控包 | `quality/` 4 文件 | ✅ | REJECT 触发 + 治理拦截 + 审计链连续 |
| T0.3 | GitHub 清理 + CONTRIBUTING | 仓库合规 | ✅ | `git check-ignore` 0 个投稿文件 |
| T0.4 | 文献综述 + v1.9 论文重组 | `docs/joss/` 2 文件 | ✅ | 真实 PMID/DOI；独立 Related Work |

### Phase 1 — 打包与硬化（无阻塞，优先级 ★★★）

| ID | 任务 | 交付物 | 优先级 | 阻塞 | 验收标准 |
|----|------|--------|--------|------|----------|
| T1.1 | 编写 pytest 套件 | `tests/test_scorer.py` + `tests/test_quality.py` | ★★★ | 无 | 覆盖：确定性（seed=42）、REJECT 路径、治理拦截 5 类、审计链重算一致 |
| T1.2 | 接入包与插件发现 | `setup.py` entry_points + `bioresearch/__init__.py` 导出 | ★★★ | 无 | `pip install -e .` 后 `import bioresearch` 成功；`PluginRegistry` 可经 entry_points 发现 demo |
| T1.3 | 纯合成 demo Scorer | `demo_plugins/trivial_scorer.py` | ★★☆ | 无 | **只用 fake 证据层**（随机/固定值），零 VCIS/AD-VCP/发表数据；实现 `EvidenceScorer` 并注册 |
| T1.4 | README 补 scorer + 质控文档 | `README.md` 新增章节 | ★★☆ | 无 | 含插件接口示例 + 质控断言清单；**无 autonomous 措辞** |

### Phase 2 — 确定性编排硬化（无 LLM，优先级 ★★☆）

| ID | 任务 | 交付物 | 优先级 | 阻塞 | 验收标准 |
|----|------|--------|--------|------|----------|
| T2.1 | 可续跑运行态硬化 | `bio-research-os/core/state.py` + `runtime.py` 增强 | ★★☆ | 无 | 8 阶段流程状态可持久化 + 断点续跑（**确定性持久化，非自进化**） |
| T2.2 | 黄金流程矩阵文档化 | `skills/` 参考 + `docs/golden_paths.md` | ★★☆ | 无 | ENCODE / GATK / MR-Base / Coloc-SuSiE 各含不可绕过质控点 |
| T2.3 | 阴性结果引擎硬化 | `engines/negative_result.py` | ★☆☆ | 无 | Evidence Package 显式标注 null 结果，不静默丢弃 |

### Phase 3 — AD-VCP 私有插件（独立仓，优先级 ★★☆）

| ID | 任务 | 交付物 | 优先级 | 阻塞 | 验收标准 |
|----|------|--------|--------|------|----------|
| T3.1 | VCIS 封装为插件 | `ad-vcp-private/plugins/vcis/vcis_scorer.py` | ★★☆ | 私有仓 | `VCISScorer(EvidenceScorer)` 通过 `validate_layers` |
| T3.2 | PCM + CAH 私有模块 | `population_constraint.py` + `constraint_theory.py` | ★★☆ | 私有仓 | 六维度约束可计算，不进公开仓 |
| T3.3 | VCIS 基准测试 | `benchmark.py`（真实 AD-VCP 数据） | ★☆☆ | 受控数据 | PR/Top-k 在私有仓跑通，**结果不公开** |

### Phase 4 — 明确拒绝（不排期）

| ID | 内容 | 拒绝理由 |
|----|------|----------|
| T4.1 | Meta-Harness 自进化 | 定位冲突 + CI 密钥安全违规 |
| T4.2 | PI 决策引擎（自主） | 定位冲突 + 不可验证 overclaim |
| T4.3 | SAS 子 Agent 集群 | 定位冲突 |
| T4.4 | CMR 跨模型路由 | 超 scope + 密钥/成本 |
| T4.5 | 自动论文生成 | 诚实/no-overclaim 违规 |
| T4.6 | VCIS 进公开仓 | 用户最新澄清：公开仓不含个人研究数据 |

---

## 5. 诚信与治理护栏（贯穿所有任务）

1. **证据分级**：A/B = 真实公共数据；C = 合成/离线。所有 Evidence Package 带 `evidence_grade`。
2. **数据治理**：`quality/governance.py` 黑名单（metabrain/ukb-ppp/adni/decode/personal_genome）硬拦截，与 `DATA_GOVERNANCE.md` 对齐。
3. **可复现**：固定 `seed=42`；所有分析记录环境 + 数据哈希。
4. **无私人数据外泄**：公开仓只含通用接口 + 合成 demo；VCIS/AD-VCP 真实数据仅在私有仓。
5. **无密钥入公共 CI**：任何需要 LLM 的能力不在公开框架内；若未来要做，必须在私有仓 + secret 管理。
6. **无 overclaim**：README/论文禁用 `agi / autonomous-agent / ai-scientist`；只陈述今天能验证的事实。

---

## 6. 下一步建议（待你确认）

- **(a)** 先收 Phase 1（T1.1–T1.4）：补齐测试 + 打包 + 合成 demo + README，让 B+C 交付成为可安装、可验证的正式模块 → 然后 `commit + push` 到 `origin/main`。
- **(b)** 若需把 v1.9 论文中文版补齐（前期只写了 en），可另开任务。
- **(c)** AD-VCP 私有的 VCIS 插件（Phase 3）需在你确认私有仓路径后启动，不在本仓库操作。

**推荐先做 (a)**——它把已验证的 B+C 代码变成正式、可发布的模块，且不触碰任何红线。确认后我即开工。
