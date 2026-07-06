# BioResearch Agent Framework

> **一个可运行的生物医学 LLM 工具框架：通过模块化智能体与引擎，执行结构化的端到端科研工作流。**

[![CI](https://github.com/Alim430/bioresearch-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Alim430/bioresearch-agent/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![v1.0.0](https://img.shields.io/badge/release-v1.0.0-green.svg)](https://github.com/Alim430/bioresearch-agent/releases/tag/v1.0.0)

---

## 🖼️ 它能产出什么（Hero Showcase）

一张图看完全部三种工作流的真实输出 —— 无需读文字，3 秒明白「这是什么」：

<div align="center">

![BioResearch Agent Output Gallery](assets/figure3_output_gallery.png)

*左：文献共现知识图谱 · 中：差异表达火山图 · 右：MR 散点图 —— 覆盖文献 / 标志物 / 因果三大场景。*

</div>

---

## ⚡ 10 秒上手

```bash
# 1. 克隆并安装
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .

# 2. 环境自检
bioresearch doctor

# 3. 跑通三个真实工作流
bioresearch run literature --query "microglia Alzheimer's disease"
bioresearch run biomarker --disease "Parkinson's disease"
bioresearch run causal   --exposure BMI --outcome "Type 2 Diabetes"

# 4. 查看输出
ls outputs/literature/ outputs/biomarker/ outputs/causal/
```

**Demo 无需任何 LLM Key** —— 使用公开 API + 合成回退数据即可运行。

---

## 🔄 端到端科研流程

从一句自然语言问题，到发表就绪的图表与报告，全流程如下：

![BioResearch Agent End-to-End Workflow](assets/bioresearch_pipeline.svg)

**核心设计：** 能力沉淀在「推理层」（抽象、模型无关），方法放在「插件层」（可替换、领域专属），工作流串联二者。12 个生命周期阶段各自带门控：`PASS` 推进 · `REVISE` 回环 · `FAIL` 中止并给出原因。

## 🔁 12 阶段生命周期

三大智能体与 6 引擎在 12 个生命周期阶段中协作，每阶段带门控检查：

<div align="center">

![12-Stage Lifecycle](assets/figure2_lifecycle.png)

*宽幅流水线图，点击查看大图。*

</div>

---

## 🏗️ 架构：五层抽象

<div align="center">

![Five-Layer Architecture](assets/figure1_framework.png)

</div>

| 层 | 职责 |
|:---|:---|
| **User Interface** | CLI · Python SDK · LLM 工具（Claude / Cursor / LangChain） |
| **Workflow** | literature / biomarker / causal（可扩展） |
| **Reasoning · 6 Engines** | Question → Retrieval → Analysis → Evidence → Narrative → Execution |
| **Lifecycle · 12 Stages** | Ideation → … → Publication，每阶段带门控 |
| **Plugin** | PubMed · GEO · KEGG · GO · GWAS · DESeq2 · IVW-MR |

---

## 🎯 它是什么

**BioResearch Agent Framework** 是一个**可运行的 AI 系统**，通过结构化推理工作流，自动化端到端生物医学研究。

| 能力（推理层） | 说明 |
|:---|:---|
| 生物医学文献推理 | 实体抽取、知识图谱构建、研究空白识别 |
| 组学数据解读 | 基因表达 / 变异 / 分子谱统计分析与生物学语境化 |
| 生物系统因果推断 | 孟德尔随机化与因果发现 |
| 多模态证据整合 | 文献 + 统计 + 机制证据 → 统一置信度评估 |
| 假说生成与验证 | 跨域证据构建可证伪假说 |
| 科学叙事综合 | 带证据分级、引用管理与图表产出的结构化报告 |

**关键差异：** 我们不只是生成文字，而是跑**完整管线** —— 数据检索、统计分析、证据分级、发表就绪输出。

---

## 🚀 三个命令，三个真实工作流

### 1. Literature Review
```bash
bioresearch run literature --query "microglia Alzheimer's disease"
```
PubMed 检索 → 摘要抽取 → 实体共现知识图谱 → 启发式空白识别 → 结构化综述大纲。
**输出：** `lit_review_summary_table.csv` · `lit_review_knowledge_graph.png` · `lit_review_knowledge_gaps.txt` · `lit_review_outline.md`

### 2. Biomarker Discovery
```bash
bioresearch run biomarker --disease "Parkinson's disease"
```
GEO 数据集（GSE7621）或合成数据 → 差异表达（t-test + Bonferroni）→ 超几何通路富集（KEGG/GO）→ 候选排序 → 火山图。
**输出：** `biomarker_deg_table.csv` · `biomarker_top_candidates.csv` · `biomarker_pathway_enrichment.csv` · `biomarker_volcano_plot.png` · `biomarker_report.txt`

### 3. Causal Inference (MR)
```bash
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
```
模拟 GWAS 汇总统计 → 全基因组显著 SNP 工具变量 → IVW 估计 → Leave-one-out 敏感性分析 → MR 散点 / 漏斗图。
**输出：** `causal_ivw_results.csv` · `causal_loo_results.csv` · `causal_mr_scatter.png` · `causal_mr_funnel.png` · `causal_interpretation.txt`

---

## 📊 输出图鉴

| 工作流 | 代表性图表 | 大小 |
|:---|:---|:---:|
| Literature | 实体共现知识图谱（40 实体 / 30 摘要） | 视分辨率 |
| Biomarker | 发表级火山图（DEG 分析） | 86 KB |
| Causal | MR 散点图（IVW slope 标注）+ 漏斗图 | 127 KB |

> 知识图谱为高清网络图，建议在本地 `outputs/literature/` 查看；其余图表均 < 1 MB，可直接预览。

---

## 🆚 为什么选它

| 任务 | 手动 | ChatGPT / Claude | BioResearch Agent |
|:---|:---:|:---:|:---:|
| 文献综述（20 篇） | 4–6 小时 | 5 分钟（仅文本） | **1.5 分钟**（报告 + 图谱 + 空白） |
| 标志物发现 | 1–2 天 | 无法访问 GEO / 跑统计 | **3 分钟**（端到端） |
| 因果推断（MR） | 1–2 小时 | 无 MR 能力 | **2 分钟**（分析 + 图） |

**每个输出都经证据分级（A–E）**，每个阶段都有门控检查，每个主张都可追溯到数据。

---

## 📦 安装

```bash
# 方式一：源码安装（当前）
git clone https://github.com/Alim430/bioresearch-agent.git
cd bioresearch-agent
pip install -e .

# 方式二：pip（发布后）
pip install bioresearch-agent
```
**依赖：** Python 3.9+，pandas · numpy · scipy · matplotlib · requests · networkx

### 环境自检
```bash
bioresearch doctor
```
校验 Python 版本、依赖、demo 文件、网络连通性与输出目录权限。

---

## 🎮 使用：三层接入

### Layer 1 · CLI（80% 用户）
```bash
bioresearch run literature --query "microglia Alzheimer's disease"
bioresearch run biomarker --disease "Parkinson's disease"
bioresearch run causal   --exposure BMI --outcome "Type 2 Diabetes"
bioresearch doctor
```

### Layer 2 · Python SDK
```python
from bioresearch import Agent

agent = Agent()
result = agent.run(
    workflow="literature",
    query="microglia Alzheimer's disease",
    output_dir="outputs/literature",
)

print(result.success)      # True
print(result.report_path)  # outline.md 路径
print(result.figures)      # ["knowledge_graph.png"]
```

### Layer 3 · LLM 工具集成
可作为 Claude Desktop / Cursor / LangChain / 任意 OpenAI 兼容函数调用系统的工具注册：
```json
{
  "name": "bioresearch_run",
  "description": "Execute biomedical research workflows",
  "parameters": {
    "workflow": "literature | biomarker | causal",
    "query": "research topic (for literature)",
    "disease": "disease name (for biomarker)",
    "exposure": "exposure trait (for causal)",
    "outcome": "outcome trait (for causal)"
  }
}
```
完整工具规范见 `bioresearch/toolspec.json`。

---

## 📂 项目结构

```
bioresearch-agent/
├── bioresearch/              # SDK + CLI 包
│   ├── __init__.py           # Agent 类
│   ├── cli.py                # bioresearch CLI
│   ├── __main__.py           # python -m bioresearch
│   └── toolspec.json         # LLM 工具规范
├── bio-research-os/          # 核心框架
│   ├── core/                 # Router / State / Orchestrator
│   ├── engines/              # 6 个研究引擎（推理层）
│   ├── demos/                # 3 个可运行工作流
│   └── examples/             # SDK 用法示例
├── outputs/                  # 生成输出（gitignored）
├── assets/                   # 文档配图
├── README.md                 # 本文件
├── RELEASE_NOTES.md          # v1.0.0 发布说明
├── arxiv-abstract.md         # 论文摘要
├── setup.py / pyproject.toml
└── Makefile                  # 快捷命令
```

---

## 📄 论文

- **标题：** *BioResearch Agent: A Tool-First Multi-Agent Framework for Biomedical Research Automation*
- **摘要：** 见 `arxiv-abstract.md`
- **目标：** arXiv (cs.AI, q-bio.QM) → NeurIPS / ICML AI for Science Workshop

---

## 🛣️ 路线图

| 阶段 | 特性 | 状态 |
|:---|:---|:---:|
| **Now** | 3 个可运行工作流（literature / biomarker / causal） | ✅ |
| **Now** | 统一 CLI（`bioresearch run`） | ✅ |
| **Now** | SDK（`Agent.run()`） | ✅ |
| **Now** | 环境自检（`bioresearch doctor`） | ✅ |
| **Now** | LLM 工具规范（`toolspec.json`） | ✅ |
| **Next** | LLM 适配器（OpenAI / Claude / 本地） | 🔜 |
| **Next** | 工作流 YAML 配置 | 🔜 |
| **Future** | 插件生态（新数据源 & 分析方法） | 📋 |
| **Future** | 多智能体协作（审稿 / 编辑智能体） | 📋 |

---

## 📜 License

MIT

---

> **BioResearch Agent Framework** —— *From hypothesis to publication, one command.*
