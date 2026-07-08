# Skill-style Interface Layer

The system can be packaged as a *skill-style interface*, enabling integration with
LLM agents through standard tool-calling conventions (e.g., OpenAI-style or
Claude-style function calling). A skill package defines a standardized manifest that
maps natural-language intents to the system's deterministic workflows — literature
review, biomarker discovery, and causal inference.

This layer does **not** introduce new computational capability. Instead, it provides a
structured interface over the existing CLI and Python SDK, improving usability and
integration with external agent frameworks. The mapping from intent to workflow is
deterministic: a `workflow` argument selects one of the three supported pipelines, and
the skill invokes the same underlying execution engine as the CLI and SDK.

## Package structure

The skill package is distributed as a self-contained directory (`skills/bioresearch/`)
containing:

- `manifest.json` — the skill descriptor; declares the entry point
  (`bioresearch.Agent.run`) and the three supported capabilities.
- `tools.json` — a model-agnostic tool schema (JSON Schema) describing input parameters
  and the output contract, reusable by any tool-calling LLM.
- `instructions.md`, `examples.md` — usage guidance and invocation examples for agents.
- `entry.py` — a thin wrapper that routes a skill call to the corresponding workflow via
  the existing `Agent.run` interface.

No runtime extension mechanism, plugin registry, or dynamic loading is introduced; the
skill package is a packaging and interface layer only.

## Usage

Using the skill requires no additional configuration beyond the underlying
installation. An LLM agent imports the skill manifest (or its tool schema) and invokes a
workflow directly:

> Import the skill package → call the workflow (`literature` / `biomarker` / `causal`)
> → receive the same deterministic outputs (report, figures, tables) as the CLI and SDK.

We provide a skill-style interface that wraps the CLI and SDK into a standardized
tool-calling format, enabling LLM agents to invoke biomedical research workflows by
**importing the skill package and using it directly**, without modifying the core
system. The interface is intentionally minimal: setup is limited to making the
underlying `bioresearch` package available, after which the skill is ready to use.

## Relation to the core system

| Aspect            | Core system            | Skill interface        |
| ----------------- | ---------------------- | ---------------------- |
| Computation       | Workflow engines       | None (delegates)       |
| Interface         | CLI, Python SDK        | Tool-calling format    |
| Extensibility     | Fixed workflows        | Fixed workflows        |
| Status            | Primary                | Packaging layer        |

The skill interface is therefore a presentation and integration layer, not a runtime
extension of the system.

## Writing discipline (reviewer-safe)

To avoid over-claiming, the skill interface is described only as a usage/packaging
layer. The following terms are intentionally **avoided** in all associated material:

- ❌ "plugin ecosystem" / "plugin system"
- ❌ "runtime extensibility framework"
- ❌ "users can dynamically extend the system"
- ❌ "skill marketplace" / "skill execution engine"

Allowed phrasing is limited to: *"provides a skill-style interface"*,
*"can be wrapped as a reusable skill package"*, and *"enables LLM tool integration via
a standardized manifest."*
