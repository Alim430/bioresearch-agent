# Reviewer-Risk Checklist (simulated rebuttal)

| # | Risk raised by reviewer | Our mitigation | Status |
|---|---|---|---|
| 1 | "plugin architecture" claimed but no dynamic plugin registry | Removed "plugin"; now "modular workflow engines" | fixed in abstract |
| 2 | "empirical evaluation demonstrates reduction in manual effort" = unsupported benchmark | Reframed as design capability; no quantitative efficiency claim | fixed |
| 3 | "multi-agent framework" overstates agency | Repositioned as "reproducible workflow engine" | fixed |
| 4 | Reproducibility unverified | Reproducibility Statement: CI py3.9–3.12 + seed-42 determinism + mock mode | verifiable |
| 5 | Depends on paid LLM / network | Mock mode default; no API key needed for demo | verifiable |
| 6 | Data-source claims (GEO / GWAS) unbacked | Clarified simulated-by-default; real datasets pluggable | clarified |
| 7 | Skills layer implied in v1.0 | Explicitly excluded from submission (v1.2 design only) | excluded |

Golden rule for any further edits during freeze: use "implements / provides /
supports / demonstrates / enables reproducible pipelines". Avoid efficiency,
plugin, ecosystem, or "AI revolution" language.
