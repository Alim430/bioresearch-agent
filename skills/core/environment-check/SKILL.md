---
name: bioresearch-environment-check
description: Verify the BioResearch Agent framework installation, Python/dependency versions, network access to biomedical databases, and output-directory permissions. Use when the user asks to validate the environment, troubleshoot a failed workflow run, or before running any analysis.
---

# BioResearch Agent — Environment & Reproducibility Check

## Capability

Validates that the framework is correctly installed and runnable, and that the reproducibility
preconditions (dependencies, network, writable outputs) are met. This is the prerequisite skill
before any literature / biomarker / causal workflow.

## Run

```bash
bioresearch doctor
```

The check validates:
- Python version (3.9+)
- Required dependencies (pandas, numpy, scipy, matplotlib, requests, networkx)
- Demo input files present
- Network connectivity to public biomedical APIs
- Output-directory write permissions

## Outputs

Console report only — no data files. Exit code `0` means ready; non-zero means a precondition
failed and should be fixed before running workflows.

## Note

Skills are thin invocation wrappers. This skill dispatches to the framework's `doctor` command;
it makes no network calls itself.
