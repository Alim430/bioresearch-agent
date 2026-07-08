---
name: bioresearch-introduction
description: Describe the BioResearch Agent Framework and its capabilities to a user or agent. Use when the user asks "what can BioResearch Agent do", wants an overview of available workflows, or is deciding which skill to invoke for a biomedical research task.
---

# BioResearch Agent — Framework Introduction

## What this skill is

A reference skill that explains the BioResearch Agent Framework's capabilities. It adds **no
analysis of its own** — it only describes what the framework can do and points to the right
workflow skill.

## Capabilities at a glance

| Capability | Workflow | Entry point |
|:---|:---|:---|
| Literature review + knowledge graph | `literature` | `bioresearch run literature --query "..."` |
| Biomarker discovery (DEG + enrichment) | `biomarker` | `bioresearch run biomarker --disease "..."` |
| Differential expression (DEG) | `biomarker` | `bioresearch run biomarker --disease "..."` |
| Pathway / GO / KEGG enrichment | `biomarker` | `bioresearch run biomarker --disease "..."` |
| Mendelian randomization (MR) | `causal` | `bioresearch run causal --exposure X --outcome Y` |
| Environment / reproducibility check | `doctor` | `bioresearch doctor` |

## Run

No computation. This skill informs; the actual work is done by the workflow skills
(`bioresearch-literature-analysis`, `bioresearch-biomarker-discovery`,
`bioresearch-differential-expression`, `bioresearch-pathway-enrichment`,
`bioresearch-causal-inference`, `bioresearch-environment-check`).

## Honesty note

BioResearch Agent executes **reproducible workflows** (t-test + Bonferroni, hypergeometric
enrichment, IVW-MR) by dispatching to existing domain libraries. It does not reason about
biology and does not discover novel science on its own.
