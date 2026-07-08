# Reproducibility Statement

All three biomedical workflows can be executed end-to-end without external API keys
or network access, and produce a fixed, structured output contract.

## Continuous integration
- `cli-smoke`: runs the literature, biomarker, and causal workflows across
  Python 3.9, 3.10, 3.11, 3.12 (`ubuntu-latest`).
- `sdk-test`: instantiates `Agent()` and calls `Agent.run(...)` for all three
  workflows; asserts the output contract (`success`, `report_path`, `tables`,
  `figures`).
- `determinism`: runs the causal workflow twice with `--seed 42`; verifies the two
  runs produce an identical output-file structure (no divergence / crash).

## Determinism
- The causal workflow accepts `--seed` (default 42). With a fixed seed, output
  structure is reproducible across runs.
- Literature (`--use-mock`) and biomarker (`--use-synthetic`) workflows run on
  deterministic local fixtures, requiring no network.

## LLM independence
- `Agent` defaults to `llm="mock"`; no commercial LLM is required to reproduce the
  demo outputs. Real LLM backends are optional
  (`pip install bioresearch-agent[llm]`).

## Output contract
Every workflow returns `success`, `error`, `summary`, `report_path`, `tables[]`,
`figures[]` — enabling exact, programmatic verification in CI.
