# Git Workflow — BioResearch Agent Framework

> Optimized branching / commit / release workflow for this repository.
> Companion to `CONTRIBUTING.md` (scope & honesty) and `DATA_GOVERNANCE.md` (data tiers).

Status: ✅ adopted · 📌 enforced by CI + branch protection · ⛔ explicitly out of scope

---

## 0. Why this document exists (diagnosis)

The repo accumulated workflow debt. Measured on `main` (2026-07-16):

| Symptom | Evidence | Fix |
|---------|----------|-----|
| Version identity crisis | README badge `v1.8.0`, `setup.py` `1.9.0`, `pyproject.toml` `1.1.0` — three values, none matching a real tag | Single source of truth = `pyproject.toml` (`1.9.0`); README badge → dynamic latest release |
| Dual packaging config | both `setup.py` and `pyproject.toml` tracked | `pyproject.toml` canonical; `setup.py` → 3-line shim |
| Submission material in Git | 5× `v1.0.0-arxiv*` tags + branches `docs/arxiv-public`, `docs/arxiv-submission`, `feat/skills-layer` | Delete (see §6); CI `guard` job blocks re-entry |
| No issue/PR templates, no CODEOWNERS | `.github/` had only `ci.yml` + meta docs | Added (see §4) |
| Test suite not in CI | `tests/` existed but `ci.yml` never ran `pytest` | Added `pytest` job (see §5) |
| Stale branches never cleaned | 3 long-lived branches | Delete after confirmation (§6) |

> ✅ Already correct (do **not** "fix"): `arxiv-abstract.md` and `framework/` are
> **already gitignored** and untracked. The earlier checklist's instruction to
> "move them into `docs/`" would have *introduced* submission material into the
> public repo — that instruction is overridden by `DATA_GOVERNANCE.md`.

---

## 1. Branching model — Trunk-Based (simplified)

```
main  ─────●────●────●────●────●───   always deployable, protected
            \  /    \  /    \  /
             ●      ●      ●         short-lived feature branches
```

- **`main`** is the single long-lived branch. Always deployable. **Protected.**
- No `develop` / Git Flow — team size (solo maintainer + occasional PRs) doesn't need it.
- Short-lived branches off `main`, deleted after merge.

### Branch naming

| Prefix | Use | Example |
|--------|-----|---------|
| `feat/` | new capability, skill, workflow | `feat/scorer-vcis-adapter` |
| `fix/` | bug fix | `fix/determinism-seed` |
| `docs/` | docs only (NOT submission drafts) | `docs/readme-structure` |
| `chore/` | build, deps, housekeeping | `chore/packaging-single-source` |
| `test/` | tests only | `test/quality-assertions` |

⛔ **Submission branches are banned in this public repo.** arXiv / bioRxiv drafts
live locally or in a *private* fork. Never `docs/arxiv-*`, never `feat/skills-layer`
carrying `arxiv-abstract.md`.

---

## 2. Commit discipline — Conventional Commits

Format: `<type>(<scope>): <subject>`

| Type | When |
|------|------|
| `feat` | new user-facing capability |
| `fix` | bug fix |
| `docs` | documentation |
| `chore` | build/deps/housekeeping |
| `test` | adding/updating tests |
| `refactor` | internal restructure, same behavior |
| `ci` | workflow / automation |

Rules:
- **Atomic** — one logical change per commit, revert independently.
- **Imperative subject**, ≤ 72 chars, no trailing period.
- Body explains *why*, not *what*.
- Never force-push `main`. If you must rewrite a PR branch, use `--force-with-lease`.

---

## 3. Pull requests & review

- Even for solo work, use a PR for traceability + required CI.
- Squash-merge PRs to keep `main` linear (no merge-commit noise).
- PR template (`.github/PULL_REQUEST_TEMPLATE.md`) enforces the honesty checklist:
  no controlled-access data, no submission-prep material, `pytest` + `doctor` green.
- External contributors: require 1 review (`CODEOWNERS` → `@Alim430`).

---

## 4. Branch protection (GitHub Settings)

Set in **Settings → Branches → Branch protection rule** for `main`:

- ✅ Require a pull request before merging
- ✅ Require status checks to pass (`pytest`, `guard`, `cli-smoke`, `sdk-test`, `determinism`)
- ✅ Require linear history (no force-push to `main`)
- ✅ Require conversation resolution before merge
- ✅ CODEOWNERS review required

> These are GitHub-side settings; this file documents the intent. Apply once.

---

## 5. CI strategy (`ci.yml`)

| Job | What it verifies |
|-----|------------------|
| `cli-smoke` | `bioresearch` CLI runs on Py 3.9–3.12 (literature / biomarker / causal) |
| `sdk-test` | `Agent` SDK output contract (tables + figures exist) |
| `determinism` | same `--seed 42` → identical output **structure** across runs |
| `pytest` ⚡ new | `pytest tests/` — scorer determinism, hard assertions, governance blocklist, audit chain |
| `guard` ⚡ new | fails if any forbidden path (`bioRxiv/`, `arxiv-abstract.md`, `framework/`, `docs/joss/paper.md`, …) is tracked |

All jobs install via `pip install -e ".[dev]"`. Cache key covers both
`setup.py` and `pyproject.toml`.

> "Reproducibility" claim precision: CI proves **structural** reproducibility
> (output file layout is identical across Python versions). Numeric
> reproducibility is asserted by fixed seeds in code; if/when a numeric
> equality check is added, the claim can be upgraded to "numerically reproducible".

---

## 6. Versioning & release

### Single source of truth
`pyproject.toml` holds **all** metadata (`version`, deps, entry points, scripts).
`setup.py` is a 3-line shim that defers to it. `CITATION.cff` mirrors the version.

### Semantic versioning
- `vX.Y.Z` — **software release only** (per `RELEASE_NOTES.md`).
- `vX.Y.Z` from `main` only; tag, then GitHub Release.
- Paper-artifact corrections (fig/doc consistency, no code change) → bump patch
  and note in `RELEASE_NOTES.md`; do **not** move the tag.

### Required cleanup (⚠️ destructive — confirm before running)
Submission material leaked into Git and must be removed:

```bash
# Delete stale submission branches (local + remote)
git branch -D docs/arxiv-public docs/arxiv-submission feat/skills-layer
git push origin --delete docs/arxiv-public docs/arxiv-submission feat/skills-layer

# Delete arXiv tags
git tag -d v1.0.0-arxiv v1.0.0-arxiv-final v1.0.0-arxiv-pack \
        v1.0.0-arxiv-public v1.0.0-arxiv-public-final
git push origin --delete v1.0.0-arxiv v1.0.0-arxiv-final v1.0.0-arxiv-pack \
        v1.0.0-arxiv-public v1.0.0-arxiv-public-final
```

After cleanup, cut a clean release:

```bash
git tag -a v1.9.0 -m "v1.9.0: EvidenceScorer interface + hard quality control"
git push origin v1.9.0
```

### Zenodo DOI (P0.4)
1. In repo **Settings → Webhooks**, connect Zenodo (`https://zenodo.org/api/webhook/`).
2. On first `v*` tag, Zenodo mints a DOI.
3. Add the Zenodo badge to README top:
   `![DOI](https://zenodo.org/badge/DOI/<DOI>.svg)(https://doi.org/<DOI>)`

---

## 7. Repo hygiene guardrails

- `.gitignore` blocks: `bioRxiv/`, `arxiv-abstract.md`, `docs/publication/`,
  `framework/`, `docs/roadmap/`, `docs/joss/paper.md`.
- CI `guard` job fails the build if any of those become tracked.
- `DATA_GOVERNANCE.md` defines the data-tier classification; controlled-access
  sources (ADNI / UKB-PPP / MetaBrain / deCODE / personal genome) are never added.

---

## 8. Explicitly OUT OF SCOPE (do not build)

Per `PLAN_v3_final.md` §4 + the user's P3 list:

- ⛔ **`harness-evolution.yml`** — scheduled, unsupervised CI that edits this repo's
  own code with an API key and auto-opens PRs. Real security + quality risk for a
  public repo maintained by an individual. (No self-modifying loops.)
- ⛔ **K-Dense-style scale benchmarking** — competing on skill count / multi-agent
  orchestration complexity is unwinnable and off-mission. Moat = depth (AD
  genetics, causal-evidence chain) + rigorous validation, not coverage.
- ⛔ **Any v2.0/v3.0 architecture upgrade before P0/P1 land** — docs & code aligned,
  DOI minted, tests visible first; then scale.

---

## 9. Execution order (week plan)

```
Week 1   P0 hygiene (this doc's §0 fixes)  → clean v1.9.0 release tag
Week 1-2 P1.1-P1.3 CONTRIBUTING / issue+PR templates / test visibility   ✅ done here
Week 2   P1.4 sanity-check table · P1.5 demo GIF
Week 2-3 P2 paper.md (JOSS) → submit
then     iterate on JOSS feedback; leave §8 items alone
```
