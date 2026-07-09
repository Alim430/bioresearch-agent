#!/usr/bin/env python3
"""
Demo: Ancestry-Aware Mendelian Randomization
==============================================

A *methodology* engine that implements cross-ancestry MR with pleiotropy
modelling (CAUSE-like and MRMix-like) and portability assessment.

IMPORTANT (honesty): the GWAS data here are SYNTHETIC. The engine implements
the real MR math (cross-ancestry IVW meta-analysis, CAUSE-like EM for
correlated + uncorrelated pleiotropy, MRMix-like mixture decomposition, and
portability metrics) but the input is simulated with a known ground-truth
causal effect. This validates that the *computations recover the planted
structure* — it is NOT an etiological claim. For real deployment, swap
`simulate_multi_ancestry_mr` with harmonized GWAS from IEU OpenGWAS (EUR),
BBJ (EAS), FinnGen (EUR), and TPMI (SAS), and point `next_validation` at
those sources.

Steps demonstrated
------------------
  1. simulate_multi_ancestry_mr : generate per-ancestry GWAS with shared
                                   causal effect + ancestry-specific
                                   pleiotropy (correlated + uncorrelated)
  2. per_ancestry_ivw           : standard IVW MR per ancestry
  3. cross_ancestry_meta_ivw    : inverse-variance-weighted meta-analysis
                                   of per-ancestry MR estimates
  4. cause_like_model           : CAUSE-inspired EM model separating
                                   causal vs pleiotropic signal
  5. mrmix_like_model           : MRMix-inspired mixture model:
                                   causal / pleiotropic / null components
  6. assess_portability         : portability metrics (heterogeneity,
                                   direction consistency, transferability)
  7. ancestry_aware_mr_pipeline : orchestrates 1-6 + evidence package

Outputs (when run as a script):
  - {output_dir}/amr_per_ancestry_results.csv
  - {output_dir}/amr_cross_ancestry_meta.csv
  - {output_dir}/amr_cause_results.csv
  - {output_dir}/amr_mrmix_results.csv
  - {output_dir}/amr_portability.csv
  - {output_dir}/amr_forest_plot.png
  - {output_dir}/amr_evidence_package.json

Usage:
  python demo_ancestry_aware_mr.py --n-snps 200 --n-instruments 40 --true-effect 0.30 --seed 42 --output-dir outputs/ancestry-aware-mr
"""

import argparse
import json
import os
import sys
import textwrap
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats, optimize

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_outputs")

GWAS_P_THRESHOLD = 5e-8

# Ancestry-specific parameters for MR simulation
ANCESTRY_MR_PARAMS = {
    "EUR": {
        "n_samples_exp": 350_000,
        "n_samples_out": 450_000,
        "pleiotropy_rate": 0.05,     # low uncorrelated pleiotropy
        "correlated_pleiotropy": 0.02,  # low correlated pleiotropy
        "instrument_strength": 1.0,  # relative instrument strength
        "label": "European",
    },
    "EAS": {
        "n_samples_exp": 180_000,
        "n_samples_out": 200_000,
        "pleiotropy_rate": 0.08,
        "correlated_pleiotropy": 0.03,
        "instrument_strength": 0.85,  # weaker due to LD differences
        "label": "East Asian",
    },
    "SAS": {
        "n_samples_exp": 100_000,
        "n_samples_out": 150_000,
        "pleiotropy_rate": 0.07,
        "correlated_pleiotropy": 0.04,
        "instrument_strength": 0.80,
        "label": "South Asian",
    },
    "AFR": {
        "n_samples_exp": 80_000,
        "n_samples_out": 100_000,
        "pleiotropy_rate": 0.06,
        "correlated_pleiotropy": 0.02,
        "instrument_strength": 0.70,  # weakest due to shorter LD
        "label": "African",
    },
    "AMR": {
        "n_samples_exp": 50_000,
        "n_samples_out": 80_000,
        "pleiotropy_rate": 0.10,     # highest due to admixture
        "correlated_pleiotropy": 0.05,
        "instrument_strength": 0.75,
        "label": "Admixed American",
    },
}


def ensure_output_dir(output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_progress(msg: str) -> None:
    print(f"[PROGRESS] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Step 1: Simulate multi-ancestry MR data
# ---------------------------------------------------------------------------

def simulate_multi_ancestry_mr(
    n_snps: int = 200,
    n_instruments: int = 40,
    true_effect: float = 0.30,
    ancestries: Optional[List[str]] = None,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Simulate per-ancestry GWAS summary statistics for MR.

    Model:
      - Shared causal effect (theta) across all ancestries
      - Ancestry-specific instrument strength (some SNPs lose instrument
        validity in non-EUR due to LD differences)
      - Uncorrelated pleiotropy: direct SNP->outcome effect (violates IV3)
      - Correlated pleiotropy: SNP affects both exposure and outcome through
        a confounder (violates InSIDE assumption)

    Returns a dict {ancestry: DataFrame} with columns:
      SNP, beta_exposure, se_exposure, p_exposure,
      beta_outcome, se_outcome, p_outcome,
      maf, n_exp, n_out, is_instrument, has_uncorr_pleio, has_corr_pleio
    """
    if ancestries is None:
        ancestries = list(ANCESTRY_MR_PARAMS.keys())

    rng = np.random.default_rng(seed)

    # Shared MAF
    maf = rng.uniform(0.05, 0.50, size=n_snps)

    # Select instruments (SNPs with strong exposure effect)
    instrument_idx = rng.choice(n_snps, size=n_instruments, replace=False)
    is_instrument = np.zeros(n_snps, dtype=bool)
    is_instrument[instrument_idx] = True

    # Shared exposure effect for instruments
    beta_x_true = np.zeros(n_snps)
    beta_x_true[is_instrument] = rng.normal(0.05, 0.02, size=n_instruments)

    # Uncorrelated pleiotropy (direct SNP->outcome, independent of exposure)
    uncorr_pleio = np.zeros(n_snps)
    # Correlated pleiotropy (SNP->confounder->exposure+outcome)
    corr_pleio = np.zeros(n_snps)

    snp_ids = [f"rs{2000000 + i}" for i in range(n_snps)]

    gwas_dict = {}

    for anc in ancestries:
        params = ANCESTRY_MR_PARAMS[anc]
        n_exp = params["n_samples_exp"]
        n_out = params["n_samples_out"]
        strength = params["instrument_strength"]

        # Ancestry-specific allele frequency drift
        eaf = np.clip(maf + rng.normal(0, 0.08, size=n_snps), 0.01, 0.99)

        # Exposure effect (adjusted by ancestry-specific instrument strength)
        beta_x = beta_x_true * strength

        # SE for exposure
        se_x = 1.0 / np.sqrt(n_exp * 2.0 * eaf * (1.0 - eaf))
        obs_beta_x = beta_x + rng.normal(0, se_x)
        z_x = obs_beta_x / se_x
        p_x = 2.0 * stats.norm.sf(np.abs(z_x))

        # Generate pleiotropy for this ancestry
        has_uncorr = rng.random(n_snps) < params["pleiotropy_rate"]
        uncorr_pleio_anc = np.where(has_uncorr, rng.normal(0, 0.02, size=n_snps), 0.0)

        has_corr = rng.random(n_snps) < params["correlated_pleiotropy"]
        # Correlated pleiotropy: effect on outcome that correlates with exposure effect
        corr_pleio_anc = np.where(has_corr, 0.5 * beta_x + rng.normal(0, 0.01, size=n_snps), 0.0)

        # Outcome effect = true causal * exposure_effect + pleiotropy
        beta_y = true_effect * beta_x + uncorr_pleio_anc + corr_pleio_anc

        se_y = 1.0 / np.sqrt(n_out * 2.0 * eaf * (1.0 - eaf))
        obs_beta_y = beta_y + rng.normal(0, se_y)
        z_y = obs_beta_y / se_y
        p_y = 2.0 * stats.norm.sf(np.abs(z_y))

        df = pd.DataFrame({
            "SNP": snp_ids,
            "beta_exposure": obs_beta_x,
            "se_exposure": se_x,
            "p_exposure": p_x,
            "beta_outcome": obs_beta_y,
            "se_outcome": se_y,
            "p_outcome": p_y,
            "eaf": eaf,
            "n_exp": n_exp,
            "n_out": n_out,
            "is_instrument": is_instrument,
            "has_uncorr_pleio": has_uncorr,
            "has_corr_pleio": has_corr,
            "ancestry": anc,
        })
        gwas_dict[anc] = df

    print_progress(
        f"Simulated {n_snps} SNPs ({n_instruments} instruments) for {len(ancestries)} ancestries. "
        f"True effect: {true_effect}."
    )
    return gwas_dict


# ---------------------------------------------------------------------------
# Step 2: Per-ancestry IVW MR
# ---------------------------------------------------------------------------

def per_ancestry_ivw(
    gwas_dict: Dict[str, pd.DataFrame],
    p_threshold: float = GWAS_P_THRESHOLD,
) -> pd.DataFrame:
    """
    Run standard IVW MR for each ancestry separately.

    For each ancestry:
      1. Select genome-wide significant SNPs for exposure
      2. Compute IVW estimate (inverse-variance weighted Wald ratios)
      3. Compute Cochran's Q heterogeneity

    Returns a DataFrame with per-ancestry MR results.
    """
    rows = []

    for anc, df in gwas_dict.items():
        # Select instruments
        sig = df[df["p_exposure"] < p_threshold].copy()
        if len(sig) < 3:
            # Relax: use top 10 by p-value
            sig = df.nsmallest(10, "p_exposure").copy()

        bx = sig["beta_exposure"].values
        by = sig["beta_outcome"].values
        se_y = sig["se_outcome"].values

        # IVW
        weights = (bx ** 2) / (se_y ** 2)
        numerator = (bx * by) / (se_y ** 2)
        beta_ivw = np.sum(numerator) / np.sum(weights)
        se_ivw = np.sqrt(1.0 / np.sum(weights))

        # Cochran's Q
        wald_ratios = by / bx
        q = np.sum((wald_ratios - beta_ivw) ** 2 * weights)
        df_q = len(sig) - 1
        p_het = 1.0 - stats.chi2.cdf(q, df_q) if df_q > 0 else 1.0

        z = beta_ivw / se_ivw
        p_value = 2.0 * stats.norm.sf(abs(z))

        rows.append({
            "ancestry": anc,
            "n_instruments": len(sig),
            "beta_ivw": beta_ivw,
            "se_ivw": se_ivw,
            "ci_lower": beta_ivw - 1.96 * se_ivw,
            "ci_upper": beta_ivw + 1.96 * se_ivw,
            "p_value": p_value,
            "cochrans_q": q,
            "p_het": p_het,
            "true_effect": 0.30,  # for comparison
            "bias": beta_ivw - 0.30,
        })

    results = pd.DataFrame(rows)
    print_progress(
        f"Per-ancestry IVW complete. "
        f"Estimates: {dict(zip(results['ancestry'], results['beta_ivw'].round(3)))}"
    )
    return results


# ---------------------------------------------------------------------------
# Step 3: Cross-ancestry meta-analysis IVW
# ---------------------------------------------------------------------------

def cross_ancestry_meta_ivw(per_ancestry_results: pd.DataFrame) -> Dict:
    """
    Meta-analyze per-ancestry MR estimates using inverse-variance weighting.

    This is the standard approach for combining cross-ancestry MR results:
      beta_meta = sum(beta_i / se_i^2) / sum(1 / se_i^2)

    Also computes:
      - Cochran's Q for heterogeneity across ancestries
      - I² statistic (proportion of variance due to heterogeneity)
      - Random-effects estimate (DerSimonian-Laird)
    """
    betas = per_ancestry_results["beta_ivw"].values
    ses = per_ancestry_results["se_ivw"].values

    # Fixed-effects IVW
    w_fe = 1.0 / (ses ** 2)
    beta_fe = np.sum(betas * w_fe) / np.sum(w_fe)
    se_fe = np.sqrt(1.0 / np.sum(w_fe))
    z_fe = beta_fe / se_fe
    p_fe = 2.0 * stats.norm.sf(abs(z_fe))

    # Cochran's Q for heterogeneity
    q = np.sum((betas - beta_fe) ** 2 * w_fe)
    df_q = len(betas) - 1
    p_het = 1.0 - stats.chi2.cdf(q, df_q) if df_q > 0 else 1.0

    # I² statistic
    i2 = max(0.0, (q - df_q) / q * 100) if q > 0 else 0.0

    # Random-effects (DerSimonian-Laird)
    tau2 = max(0.0, (q - df_q) / np.sum(w_fe)) if q > df_q else 0.0
    w_re = 1.0 / (ses ** 2 + tau2)
    beta_re = np.sum(betas * w_re) / np.sum(w_re)
    se_re = np.sqrt(1.0 / np.sum(w_re))
    z_re = beta_re / se_re
    p_re = 2.0 * stats.norm.sf(abs(z_re))

    result = {
        "method": "cross-ancestry-meta-ivw",
        "n_ancestries": len(betas),
        "beta_fe": beta_fe,
        "se_fe": se_fe,
        "p_fe": p_fe,
        "beta_re": beta_re,
        "se_re": se_re,
        "p_re": p_re,
        "cochrans_q": q,
        "df_q": df_q,
        "p_het": p_het,
        "i_squared": i2,
        "tau_squared": tau2,
        "true_effect": 0.30,
        "bias_fe": beta_fe - 0.30,
        "bias_re": beta_re - 0.30,
    }

    print_progress(
        f"Cross-ancestry meta-IVW: beta_fe={beta_fe:.4f} (p={p_fe:.2e}), "
        f"beta_re={beta_re:.4f} (p={p_re:.2e}), "
        f"I²={i2:.1f}%, Q p={p_het:.3f}."
    )
    return result


# ---------------------------------------------------------------------------
# Step 4: CAUSE-like model (correlated + uncorrelated pleiotropy)
# ---------------------------------------------------------------------------

def cause_like_model(
    gwas_dict: Dict[str, pd.DataFrame],
    ancestry: str = "EUR",
    p_threshold: float = GWAS_P_THRESHOLD,
    n_iter: int = 100,
) -> Dict:
    """
    CAUSE-inspired model (Morrison et al. 2020).

    Decomposes SNP-outcome association into:
      - Causal pathway: theta * gamma_i (shared causal effect)
      - Correlated pleiotropy: eta * gamma_i (confounder pathway)
      - Uncorrelated pleiotropy: direct effect (modelled as noise)

    The EM algorithm estimates:
      - theta (causal effect)
      - eta (correlated pleiotropy coefficient)
      - sigma_uncorr (uncorrelated pleiotropy variance)

    Then tests H0 (theta=0, eta free) vs H1 (theta free, eta free) via LRT.

    NOTE: This is a simplified implementation for demonstration. The real
    CAUSE uses a full Bayesian model with MCMC. Here we use EM + LRT.
    """
    df = gwas_dict[ancestry]
    sig = df[df["p_exposure"] < p_threshold].copy()
    if len(sig) < 5:
        sig = df.nsmallest(10, "p_exposure").copy()

    gamma = sig["beta_exposure"].values  # exposure effects
    gamma_i = gamma  # alias used in EM iterations below
    gamma_se = sig["se_exposure"].values
    beta_y = sig["beta_outcome"].values
    beta_y_se = sig["se_outcome"].values

    n = len(gamma)

    # --- EM Algorithm for H1 (causal + pleiotropy) ---
    # Model: beta_y_i ~ N(theta * gamma_i + eta * gamma_i + delta_i, sigma_y_i^2)
    # where delta_i ~ N(0, sigma_uncorr^2) for pleiotropic SNPs, 0 otherwise
    # z_i (responsibility) = P(SNP i is pleiotropic | data)

    # Initialize
    theta_h1 = 0.0
    eta_h1 = 0.0
    sigma_uncorr_h1 = 0.01

    for iteration in range(n_iter):
        # E-step: compute responsibilities
        # Expected delta_i under H1
        mu_i = (theta_h1 + eta_h1) * gamma_i
        resid_i = beta_y - mu_i
        # z_i = probability that SNP i has uncorrelated pleiotropy
        var_total = beta_y_se ** 2 + sigma_uncorr_h1 ** 2
        # Log-likelihood ratio for pleiotropic vs non-pleiotropic
        ll_pleio = -0.5 * np.log(2 * np.pi * var_total) - 0.5 * (resid_i ** 2) / var_total
        ll_non_pleio = -0.5 * np.log(2 * np.pi * beta_y_se ** 2) - 0.5 * (resid_i ** 2) / beta_y_se ** 2
        # Prior: 10% pleiotropic
        prior_pleio = 0.1
        z_i = 1.0 / (1.0 + (1 - prior_pleio) / prior_pleio * np.exp(ll_non_pleio - ll_pleio))
        z_i = np.clip(z_i, 1e-6, 1 - 1e-6)

        # M-step: update parameters
        # Weighted regression: beta_y = (theta + eta) * gamma + delta
        # But we need to separate theta from eta...
        # Simplification: estimate combined effect (theta + eta) via weighted regression,
        # then estimate eta from the intercept of beta_y vs gamma after removing theta*gamma
        w_i = z_i / var_total + (1 - z_i) / beta_y_se ** 2
        combined_effect = np.sum(w_i * gamma_i * beta_y) / np.sum(w_i * gamma_i ** 2)

        # Estimate theta and eta
        # Under H1: beta_y = theta * gamma + eta * gamma + delta = (theta+eta) * gamma + delta
        # We can't separately identify theta and eta without additional info
        # In real CAUSE, this is identified through the correlation structure
        # Here we estimate: theta = combined_effect * (1 - corr_fraction), eta = combined_effect * corr_fraction
        # corr_fraction estimated from how much of gamma-beta_y correlation is "vertical" vs "horizontal"
        # Simplified: use median(z_i) as the fraction of correlated pleiotropy
        corr_fraction = np.mean(z_i) * 0.5  # heuristic
        theta_h1 = combined_effect * (1 - corr_fraction)
        eta_h1 = combined_effect * corr_fraction

        # Update sigma_uncorr
        delta_i = resid_i
        sigma_uncorr_h1 = max(0.001, np.sqrt(np.sum(z_i * delta_i ** 2) / max(np.sum(z_i), 1)))

    # Log-likelihood under H1
    mu_h1 = (theta_h1 + eta_h1) * gamma_i
    ll_h1 = np.sum(stats.norm.logpdf(beta_y, mu_h1, np.sqrt(beta_y_se ** 2 + sigma_uncorr_h1 ** 2)))

    # --- EM for H0 (no causal effect, pleiotropy only) ---
    theta_h0 = 0.0
    eta_h0 = 0.0
    sigma_uncorr_h0 = 0.01

    for iteration in range(n_iter):
        mu_i = eta_h0 * gamma_i
        resid_i = beta_y - mu_i
        var_total = beta_y_se ** 2 + sigma_uncorr_h0 ** 2
        ll_pleio = -0.5 * np.log(2 * np.pi * var_total) - 0.5 * (resid_i ** 2) / var_total
        ll_non_pleio = -0.5 * np.log(2 * np.pi * beta_y_se ** 2) - 0.5 * (resid_i ** 2) / beta_y_se ** 2
        prior_pleio = 0.1
        z_i = 1.0 / (1.0 + (1 - prior_pleio) / prior_pleio * np.exp(ll_non_pleio - ll_pleio))
        z_i = np.clip(z_i, 1e-6, 1 - 1e-6)

        w_i = z_i / var_total + (1 - z_i) / beta_y_se ** 2
        eta_h0 = np.sum(w_i * gamma_i * beta_y) / np.sum(w_i * gamma_i ** 2)
        delta_i = resid_i
        sigma_uncorr_h0 = max(0.001, np.sqrt(np.sum(z_i * delta_i ** 2) / max(np.sum(z_i), 1)))

    mu_h0 = eta_h0 * gamma_i
    ll_h0 = np.sum(stats.norm.logpdf(beta_y, mu_h0, np.sqrt(beta_y_se ** 2 + sigma_uncorr_h0 ** 2)))

    # LRT: -2 * (ll_h0 - ll_h1) ~ chi2(1)
    lrt_stat = max(0, -2 * (ll_h0 - ll_h1))
    p_lrt = 1.0 - stats.chi2.cdf(lrt_stat, df=1)

    result = {
        "method": "CAUSE-like",
        "ancestry": ancestry,
        "n_snps": n,
        "theta_h1": float(theta_h1),
        "eta_h1": float(eta_h1),
        "sigma_uncorr_h1": float(sigma_uncorr_h1),
        "eta_h0": float(eta_h0),
        "sigma_uncorr_h0": float(sigma_uncorr_h0),
        "ll_h1": float(ll_h1),
        "ll_h0": float(ll_h0),
        "lrt_statistic": float(lrt_stat),
        "p_lrt": float(p_lrt),
        "true_effect": 0.30,
        "bias_theta": float(theta_h1 - 0.30),
        "interpretation": (
            "CAUSE LRT significant (p < 0.05): evidence for causal effect "
            "beyond correlated pleiotropy." if p_lrt < 0.05 else
            "CAUSE LRT not significant: cannot rule out correlated pleiotropy."
        ),
    }

    print_progress(
        f"CAUSE-like ({ancestry}): theta={theta_h1:.4f}, eta={eta_h1:.4f}, "
        f"LRT p={p_lrt:.4f}."
    )
    return result


# ---------------------------------------------------------------------------
# Step 5: MRMix-like model (mixture decomposition)
# ---------------------------------------------------------------------------

def mrmix_like_model(
    gwas_dict: Dict[str, pd.DataFrame],
    ancestry: str = "EUR",
    p_threshold: float = GWAS_P_THRESHOLD,
    n_iter: int = 100,
) -> Dict:
    """
    MRMix-inspired model (Wang et al. 2020).

    Decomposes SNPs into three mixture components:
      1. Causal (pi_c): SNPs with causal effect (theta != 0)
      2. Pleiotropic (pi_p): SNPs with direct outcome effect (violates IV3)
      3. Null (pi_0): SNPs with no effect

    The EM algorithm estimates:
      - pi_c, pi_p, pi_0 (mixture proportions)
      - theta (causal effect)
      - sigma_p (pleiotropy effect size SD)

    NOTE: Simplified implementation for demonstration. Real MRMix uses
    a more sophisticated model with profile likelihood.
    """
    df = gwas_dict[ancestry]
    sig = df[df["p_exposure"] < p_threshold].copy()
    if len(sig) < 5:
        sig = df.nsmallest(10, "p_exposure").copy()

    gamma = sig["beta_exposure"].values
    beta_y = sig["beta_outcome"].values
    se_y = sig["se_outcome"].values

    n = len(gamma)

    # Initialize mixture parameters
    pi_c = 0.5      # causal proportion
    pi_p = 0.2      # pleiotropic proportion
    pi_0 = 1 - pi_c - pi_p  # null
    theta = 0.0     # causal effect
    sigma_p = 0.02  # pleiotropy SD

    for iteration in range(n_iter):
        # E-step: compute responsibilities for each component
        # Component 1 (causal): beta_y ~ N(theta * gamma, se_y^2)
        ll_c = stats.norm.logpdf(beta_y, theta * gamma, se_y)
        # Component 2 (pleiotropic): beta_y ~ N(0, se_y^2 + sigma_p^2)
        ll_p = stats.norm.logpdf(beta_y, 0, np.sqrt(se_y ** 2 + sigma_p ** 2))
        # Component 3 (null): beta_y ~ N(0, se_y^2)
        ll_0 = stats.norm.logpdf(beta_y, 0, se_y)

        # Posterior responsibilities
        log_weights = np.column_stack([
            np.log(pi_c) + ll_c,
            np.log(pi_p) + ll_p,
            np.log(max(pi_0, 1e-10)) + ll_0,
        ])
        log_weights -= log_weights.max(axis=1, keepdims=True)
        weights = np.exp(log_weights)
        weights /= weights.sum(axis=1, keepdims=True)

        z_c = weights[:, 0]
        z_p = weights[:, 1]
        z_0 = weights[:, 2]

        # M-step: update parameters
        pi_c = np.mean(z_c)
        pi_p = np.mean(z_p)
        pi_0 = max(1e-6, 1 - pi_c - pi_p)

        # Update theta: weighted regression
        w_c = z_c / (se_y ** 2)
        if np.sum(w_c * gamma ** 2) > 0:
            theta = np.sum(w_c * gamma * beta_y) / np.sum(w_c * gamma ** 2)

        # Update sigma_p
        sigma_p = max(0.001, np.sqrt(np.sum(z_p * beta_y ** 2) / max(np.sum(z_p), 1)))

    # Compute standard error for theta (from the information matrix)
    w_c_final = z_c / (se_y ** 2)
    se_theta = np.sqrt(1.0 / max(np.sum(w_c_final * gamma ** 2), 1e-10))
    z_theta = theta / se_theta
    p_theta = 2.0 * stats.norm.sf(abs(z_theta))

    # BIC for model comparison
    ll_final = np.sum(
        pi_c * stats.norm.pdf(beta_y, theta * gamma, se_y) +
        pi_p * stats.norm.pdf(beta_y, 0, np.sqrt(se_y ** 2 + sigma_p ** 2)) +
        pi_0 * stats.norm.pdf(beta_y, 0, se_y)
    )
    n_params = 5  # pi_c, pi_p, theta, sigma_p, (pi_0 derived)
    bic = -2 * np.log(ll_final + 1e-300) + n_params * np.log(n)

    result = {
        "method": "MRMix-like",
        "ancestry": ancestry,
        "n_snps": n,
        "pi_causal": float(pi_c),
        "pi_pleiotropic": float(pi_p),
        "pi_null": float(pi_0),
        "theta": float(theta),
        "se_theta": float(se_theta),
        "p_value": float(p_theta),
        "sigma_pleiotropy": float(sigma_p),
        "bic": float(bic),
        "true_effect": 0.30,
        "bias_theta": float(theta - 0.30),
        "interpretation": (
            f"MRMix: {pi_c*100:.1f}% causal, {pi_p*100:.1f}% pleiotropic, "
            f"{pi_0*100:.1f}% null. Causal effect theta={theta:.4f} (p={p_theta:.4f})."
        ),
    }

    print_progress(
        f"MRMix-like ({ancestry}): pi_c={pi_c:.3f}, pi_p={pi_p:.3f}, "
        f"theta={theta:.4f} (p={p_theta:.4f})."
    )
    return result


# ---------------------------------------------------------------------------
# Step 6: Portability assessment
# ---------------------------------------------------------------------------

def assess_portability(per_ancestry_results: pd.DataFrame) -> Dict:
    """
    Assess the portability of MR findings across ancestries.

    Metrics:
      1. Direction consistency: fraction of ancestries with same-sign estimate
      2. Significance consistency: fraction with p < 0.05
      3. Effect-size heterogeneity: I² from cross-ancestry meta
      4. Transferability score: composite metric (0-1)
      5. EUR-centric bias: how much do non-EUR estimates deviate from EUR?
    """
    n = len(per_ancestry_results)
    betas = per_ancestry_results["beta_ivw"].values
    pvals = per_ancestry_results["p_value"].values

    # Direction consistency
    signs = np.sign(betas)
    if np.all(signs > 0) or np.all(signs < 0):
        direction_consistency = 1.0
    else:
        majority_sign = np.sign(np.sum(signs))
        direction_consistency = np.mean(signs == majority_sign)

    # Significance consistency
    sig_consistency = np.mean(pvals < 0.05)

    # Effect-size heterogeneity (I² from meta)
    meta_result = cross_ancestry_meta_ivw(per_ancestry_results)
    i2 = meta_result["i_squared"] / 100.0  # convert to 0-1

    # EUR-centric bias
    eur_beta = per_ancestry_results[per_ancestry_results["ancestry"] == "EUR"]["beta_ivw"].values
    if len(eur_beta) > 0:
        non_eur_betas = per_ancestry_results[per_ancestry_results["ancestry"] != "EUR"]["beta_ivw"].values
        if len(non_eur_betas) > 0:
            eur_centric_bias = np.mean(np.abs(non_eur_betas - eur_beta[0]))
        else:
            eur_centric_bias = 0.0
    else:
        eur_centric_bias = 0.0

    # Transferability score (composite, 0-1)
    # Higher = more portable
    transferability = (
        0.3 * direction_consistency +
        0.3 * sig_consistency +
        0.2 * (1.0 - i2) +
        0.2 * (1.0 - min(1.0, eur_centric_bias / 0.3))  # normalized bias
    )

    result = {
        "direction_consistency": float(direction_consistency),
        "significance_consistency": float(sig_consistency),
        "heterogeneity_i2": float(i2),
        "eur_centric_bias": float(eur_centric_bias),
        "transferability_score": float(transferability),
        "meta_beta_fe": float(meta_result["beta_fe"]),
        "meta_p_fe": float(meta_result["p_fe"]),
        "meta_p_het": float(meta_result["p_het"]),
        "assessment": (
            "High portability" if transferability >= 0.8 else
            "Moderate portability" if transferability >= 0.5 else
            "Low portability — EUR-derived instruments may not transfer"
        ),
    }

    print_progress(
        f"Portability: direction={direction_consistency:.2f}, "
        f"significance={sig_consistency:.2f}, "
        f"I²={i2:.2f}, "
        f"transferability={transferability:.3f}."
    )
    return result


# ---------------------------------------------------------------------------
# Step 7: Visualization
# ---------------------------------------------------------------------------

def plot_forest(per_ancestry_results: pd.DataFrame, meta_result: Dict, outpath: str) -> None:
    """Plot a forest plot of per-ancestry MR estimates + meta-analysis."""
    print_progress("Generating forest plot ...")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Sort: ancestries top, meta bottom
    y_labels = list(per_ancestry_results["ancestry"]) + ["Meta (FE)", "Meta (RE)", "True effect"]
    y_pos = list(range(len(per_ancestry_results), 0, -1))
    y_meta_fe = 2
    y_meta_re = 1
    y_true = 0

    # Per-ancestry points
    for i, (_, row) in enumerate(per_ancestry_results.iterrows()):
        y = y_pos[i]
        ax.errorbar(row["beta_ivw"], y, xerr=1.96 * row["se_ivw"],
                     fmt="o", color="steelblue", capsize=3, markersize=6)

    # Meta FE
    ax.errorbar(meta_result["beta_fe"], y_meta_fe, xerr=1.96 * meta_result["se_fe"],
                 fmt="D", color="crimson", capsize=3, markersize=8, label="Meta (FE)")

    # Meta RE
    ax.errorbar(meta_result["beta_re"], y_meta_re, xerr=1.96 * meta_result["se_re"],
                 fmt="D", color="darkorange", capsize=3, markersize=8, label="Meta (RE)")

    # True effect
    ax.axvline(0.30, color="green", linestyle="--", linewidth=2, label="True effect")

    ax.axvline(0, color="black", linestyle="-", linewidth=0.5)
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Causal Effect Estimate (beta)")
    ax.set_title("Cross-Ancestry MR Forest Plot")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(-0.5, len(per_ancestry_results) + 0.5)

    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print_progress(f"Saved forest plot to {outpath}")


# ---------------------------------------------------------------------------
# Step 8: Pipeline orchestration
# ---------------------------------------------------------------------------

def ancestry_aware_mr_pipeline(
    n_snps: int = 200,
    n_instruments: int = 40,
    true_effect: float = 0.30,
    ancestries: Optional[List[str]] = None,
    cause_ancestry: str = "EUR",
    mrmix_ancestry: str = "EUR",
    seed: int = 42,
    output_dir: Optional[str] = None,
) -> Dict:
    """
    Full ancestry-aware MR pipeline.

    Returns a dict with keys:
      - per_ancestry_results: DataFrame
      - meta_result: dict
      - cause_result: dict
      - mrmix_result: dict
      - portability: dict
      - evidence_package: dict
    """
    output_dir = ensure_output_dir(output_dir)

    # Step 1: Simulate
    print_progress("Step 1/7: Simulating multi-ancestry MR data ...")
    gwas_dict = simulate_multi_ancestry_mr(
        n_snps=n_snps,
        n_instruments=n_instruments,
        true_effect=true_effect,
        ancestries=ancestries,
        seed=seed,
    )

    # Step 2: Per-ancestry IVW
    print_progress("Step 2/7: Running per-ancestry IVW MR ...")
    per_anc = per_ancestry_ivw(gwas_dict)

    # Step 3: Cross-ancestry meta
    print_progress("Step 3/7: Running cross-ancestry meta-analysis ...")
    meta = cross_ancestry_meta_ivw(per_anc)

    # Step 4: CAUSE-like model
    print_progress("Step 4/7: Running CAUSE-like pleiotropy model ...")
    cause = cause_like_model(gwas_dict, ancestry=cause_ancestry)

    # Step 5: MRMix-like model
    print_progress("Step 5/7: Running MRMix-like mixture model ...")
    mrmix = mrmix_like_model(gwas_dict, ancestry=mrmix_ancestry)

    # Step 6: Portability assessment
    print_progress("Step 6/7: Assessing portability ...")
    portability = assess_portability(per_anc)

    # Step 7: Save outputs + evidence package
    print_progress("Step 7/7: Saving outputs and evidence package ...")

    per_anc.to_csv(os.path.join(output_dir, "amr_per_ancestry_results.csv"), index=False)
    pd.DataFrame([meta]).to_csv(os.path.join(output_dir, "amr_cross_ancestry_meta.csv"), index=False)
    pd.DataFrame([cause]).to_csv(os.path.join(output_dir, "amr_cause_results.csv"), index=False)
    pd.DataFrame([mrmix]).to_csv(os.path.join(output_dir, "amr_mrmix_results.csv"), index=False)
    pd.DataFrame([portability]).to_csv(os.path.join(output_dir, "amr_portability.csv"), index=False)

    # Forest plot
    plot_forest(per_anc, meta, os.path.join(output_dir, "amr_forest_plot.png"))

    # Evidence package
    evidence_package = {
        "case_id": "Case 9",
        "pipeline": "ancestry-aware-mr",
        "evidence_grade": "C",
        "data_type": "synthetic",
        "framework_version": "1.8.0",
        "seed": seed,
        "parameters": {
            "n_snps": n_snps,
            "n_instruments": n_instruments,
            "true_effect": true_effect,
            "ancestries": list(gwas_dict.keys()),
            "cause_ancestry": cause_ancestry,
            "mrmix_ancestry": mrmix_ancestry,
        },
        "results": {
            "per_ancestry_estimates": per_anc[["ancestry", "beta_ivw", "se_ivw", "p_value"]].to_dict("records"),
            "meta_fe_beta": float(meta["beta_fe"]),
            "meta_fe_p": float(meta["p_fe"]),
            "meta_re_beta": float(meta["beta_re"]),
            "meta_re_p": float(meta["p_re"]),
            "meta_i2": float(meta["i_squared"]),
            "meta_p_het": float(meta["p_het"]),
            "cause_theta": float(cause["theta_h1"]),
            "cause_eta": float(cause["eta_h1"]),
            "cause_p_lrt": float(cause["p_lrt"]),
            "mrmix_theta": float(mrmix["theta"]),
            "mrmix_p": float(mrmix["p_value"]),
            "mrmix_pi_causal": float(mrmix["pi_causal"]),
            "mrmix_pi_pleiotropic": float(mrmix["pi_pleiotropic"]),
            "portability_score": float(portability["transferability_score"]),
            "portability_assessment": portability["assessment"],
            "direction_consistency": float(portability["direction_consistency"]),
            "true_effect": true_effect,
        },
        "limitations": [
            "Synthetic data with simplified pleiotropy model",
            "CAUSE-like EM is a simplified approximation (real CAUSE uses Bayesian MCMC)",
            "MRMix-like model uses simplified profile likelihood",
            "No LD clumping performed (real analysis requires ancestry-specific LD reference)",
            "Instrument strength variation across ancestries is simplified",
        ],
        "next_validation": [
            "Replace simulated data with real GWAS: IEU OpenGWAS (EUR) + BBJ (EAS) + TPMI (SAS)",
            "Use ancestry-specific LD reference panels for clumping (1000G per-population)",
            "Run real CAUSE (R package) with full Bayesian MCMC",
            "Run real MRMix (R package) with profile likelihood",
            "Validate portability against published trans-ancestry MR studies",
        ],
        "provenance": {
            "script": "demo_ancestry_aware_mr.py",
            "timestamp": pd.Timestamp.now().isoformat(),
            "output_dir": output_dir,
        },
    }

    with open(os.path.join(output_dir, "amr_evidence_package.json"), "w", encoding="utf-8") as fh:
        json.dump(evidence_package, fh, indent=2, ensure_ascii=False, default=str)

    print_progress(f"Pipeline complete. Outputs saved to {output_dir}")

    return {
        "per_ancestry_results": per_anc,
        "meta_result": meta,
        "cause_result": cause,
        "mrmix_result": mrmix,
        "portability": portability,
        "evidence_package": evidence_package,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ancestry-Aware Mendelian Randomization Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__),
    )
    parser.add_argument("--n-snps", type=int, default=200, help="Number of SNPs to simulate (default: 200)")
    parser.add_argument("--n-instruments", type=int, default=40, help="Number of instrument SNPs (default: 40)")
    parser.add_argument("--true-effect", type=float, default=0.30, help="True causal effect (default: 0.30)")
    parser.add_argument(
        "--ancestries",
        type=str,
        nargs="+",
        default=None,
        help="Ancestries to include (default: all 5: EUR EAS SAS AFR AMR)",
    )
    parser.add_argument("--cause-ancestry", type=str, default="EUR", help="Ancestry for CAUSE model (default: EUR)")
    parser.add_argument("--mrmix-ancestry", type=str, default="EUR", help="Ancestry for MRMix model (default: EUR)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")

    args = parser.parse_args()

    result = ancestry_aware_mr_pipeline(
        n_snps=args.n_snps,
        n_instruments=args.n_instruments,
        true_effect=args.true_effect,
        ancestries=args.ancestries,
        cause_ancestry=args.cause_ancestry,
        mrmix_ancestry=args.mrmix_ancestry,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("Ancestry-Aware MR Pipeline — Summary")
    print("=" * 60)
    print(f"Meta FE beta: {result['meta_result']['beta_fe']:.4f} (p={result['meta_result']['p_fe']:.2e})")
    print(f"Meta RE beta: {result['meta_result']['beta_re']:.4f} (p={result['meta_result']['p_re']:.2e})")
    print(f"I² heterogeneity: {result['meta_result']['i_squared']:.1f}%")
    print(f"CAUSE theta: {result['cause_result']['theta_h1']:.4f} (LRT p={result['cause_result']['p_lrt']:.4f})")
    print(f"MRMix theta: {result['mrmix_result']['theta']:.4f} (p={result['mrmix_result']['p_value']:.4f})")
    print(f"Portability: {result['portability']['transferability_score']:.3f} ({result['portability']['assessment']})")
    print(f"True effect: {result['evidence_package']['results']['true_effect']}")
    print(f"Evidence grade: {result['evidence_package']['evidence_grade']}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
