# BioResearch Agent Skills

Reusable **workflow skill definitions** that let an AI assistant run real biomedical pipelines
(literature analysis, biomarker discovery, causal inference) through the BioResearch Agent
framework. These are *interface wrappers, not reasoning modules*: they carry invocation
instructions and parameter schemas only — all computation runs in the framework's workflow modules.

## Supported environments

Drop the skill folders into your client's skill directory. Compatible with any
[Agent Skills](https://agentskills.io)–compatible client, including:

- ✅ Claude Code
- ✅ Claude Desktop
- ✅ Cursor
- ✅ Codex CLI
- ✅ Other Agent Skills–compatible systems

## Available skills

| Skill | Pipeline | What it invokes |
|:---|:---|:---|
| `literature` | Literature review | PubMed retrieval + entity co-occurrence graph |
| `biomarker` | Biomarker discovery | Differential expression + pathway enrichment |
| `causal` | Causal inference | Mendelian randomization (IVW) |

## Install (recommended)

From the repository root:

```bash
./skills/install.sh
```

The installer detects your agent's skill directory, copies the three skills, and verifies the
framework with `bioresearch doctor`.

## Manual install

```bash
# Claude Desktop (macOS)
cp -r skills/literature skills/biomarker skills/causal \
  "$HOME/Library/Application Support/Claude/skills/"

# Claude / generic (~/.config)
cp -r skills/literature skills/biomarker skills/causal ~/.config/agent/skills/

# Cursor
cp -r skills/literature skills/biomarker skills/causal ~/.cursor/skills/
```

Restart the client after copying.

## How it works

```
AI assistant
     │  (triggers a skill by description match)
     ▼
Skill (SKILL.md)  ── dispatches to ──▶  bioresearch CLI/SDK
                                         │
                                         ▼
                              reproducible workflow modules
                              (real DEG / MR / PubMed analysis)
```

Each skill delegates to the `bioresearch` command. The assistant never performs the analysis
itself — it executes a validated, reproducible pipeline and returns the data-derived outputs.

See the top-level [README](../README.md) for the full framework architecture and the
[Data & Network Access](../README.md#-data--network-access) section for exactly which external
resources each workflow contacts.
