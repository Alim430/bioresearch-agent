# Example — Mendelian Randomization: BMI → Type 2 Diabetes

**Goal:** Test the causal effect of BMI on Type 2 Diabetes using two-sample Mendelian randomization, and return the IVW estimate with sensitivity plots.

## Via AI assistant (after installing the `causal` skill)

> **You:** Test whether BMI causally affects Type 2 Diabetes.

> **Assistant:** Running the `bioresearch` causal (MR) workflow…
> - Generated/loaded GWAS summary stats (simulated by default)
> - Selected genome-wide significant SNP instruments
> - Estimated causal effect via IVW
> - Ran leave-one-out sensitivity analysis
>
> Outputs written to `outputs/causal/`:
> - `causal_ivw_results.csv`
> - `causal_loo_results.csv`
> - `causal_mr_scatter.png`
> - `causal_mr_funnel.png`
> - `causal_interpretation.txt`

## Via CLI (same engine)

```bash
bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
```

## What it actually does

GWAS summary stats → instrument selection (genome-wide significant SNPs) → IVW estimation →
leave-one-out sensitivity → scatter / funnel plots. By default the demo uses simulated GWAS data
so it runs without external credentials; point it at real summary Statistics to reproduce
published MR.

See a sample MR scatter plot: `assets/figure3_output_gallery.png` (right panel) or
`outputs/causal/causal_mr_scatter.png`.
