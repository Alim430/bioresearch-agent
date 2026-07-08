# BioResearch Skill — LLM Integration Guide

This skill is **model-agnostic**. The same `tools.json` schema is consumable by
Claude, GPT/OpenAI, Cursor, and local LLM runtimes without modification. We do
**not** hard-code any vendor, and we do **not** rely on a proprietary "skills
format" — the skill is just a tool definition + instructions + a thin runtime
wrapper. That keeps it portable across the evolving tool-calling ecosystem.

> **Status:** v1.1 design, `feat/skills-layer` branch. Not in the frozen v1.0.0 `main`.

---

## 0. The universal rule

Whatever client you use, register **one tool** `bioresearch_run` from
`tools.json`. The client calls it; the Python runtime (`bioresearch.Agent`)
executes the workflow and returns the structured output contract.

The schema uses `allOf`/`if`/`then` conditional-required (JSON-Schema draft-07),
which Claude, OpenAI, and LangChain all parse.

---

## 1. OpenAI function calling

```python
import openai  # or any OpenAI-compatible client
from skills.boresearch.entry import run  # see note below
import json

# Load the tool schema
with open("skills/bioresearch/tools.json") as f:
    tool = json.load(f)["tools"][0]

messages = [{"role": "user", "content": "Review literature on microglia in Alzheimer disease"}]

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[tool],
    tool_choice="auto",
)

# When the model calls bioresearch_run, execute it locally:
if resp.choices[0].message.tool_calls:
    args = json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
    result = run(**args)  # thin wrapper -> Agent.run
    # feed result.report_path / tables / figures back to the model
```

> Note: `skills.bioresearch.entry` must be importable — add `skills/bioresearch`
> to `sys.path`, or call `bioresearch.Agent().run(...)` directly.

---

## 2. Claude (Anthropic) tool use

Claude's tool format is the same JSON-Schema. Pass `tools.json`'s `bioresearch_run`
directly:

```python
import anthropic

client = anthropic.Anthropic()
tool = json.load(open("skills/bioresearch/tools.json"))["tools"][0]

msg = client.messages.create(
    model="claude-opus-4",
    max_tokens=1024,
    tools=[tool],
    messages=[{"role": "user", "content": "Run a Mendelian randomization: BMI -> Type 2 Diabetes"}],
)
# On a tool_use block, execute locally and return a tool_result with
# result.report_path / tables / figures.
```

---

## 3. Cursor

Cursor can call the CLI directly, or register the tool via project rules.

**Option A — CLI tool (simplest, zero Python glue):**
Add a `.cursor/rules/bioresearch.mdc` (or project rule) telling Cursor it may run:

```bash
bioresearch run <workflow> --<arg> ...
```

**Option B — register as an agent tool:** point Cursor at `skills/bioresearch/`
so it ingests `tools.json` + `instructions.md` and exposes `bioresearch_run`.
Cursor then calls the local runtime the same way as §1/§2.

---

## 4. MCP server (optional, stdio)

If you want first-class MCP support, wrap `bioresearch_run` in a tiny stdio
server. This is **optional** for v1.1 — the static skill already works with any
tool-calling client. Minimal skeleton:

```python
# mcp_server.py (optional)
import json, sys
from skills.bioresearch.entry import run

def handle(call):
    args = call["params"].get("arguments", {})
    r = run(**args)
    return {
        "report_path": r.report_path,
        "tables": r.tables,
        "figures": r.figures,
        "success": r.success,
        "error": r.error,
    }

# ... wire to an MCP stdio transport (e.g. the official mcp python SDK) ...
```

Register the server in the client's MCP config; the tool name stays
`bioresearch_run`.

---

## 5. Industry-safe wording

Do **not** advertise vendor-specific tags as a feature claim. The portable
description is:

> *Compatible with any tool-calling LLM (Claude, Cursor, OpenAI-compatible
> agents, and local LLM runtimes).*

This avoids marketing overreach and keeps the skill usable regardless of which
model the user runs.
