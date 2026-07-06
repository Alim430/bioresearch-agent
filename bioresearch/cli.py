"""
BioResearch Agent Framework — Unified CLI Entry Point

Usage:
    bioresearch run literature --query "microglia Alzheimer's disease"
    bioresearch run biomarker --disease "Parkinson's disease"
    bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
    bioresearch doctor              # Check environment health
    bioresearch --help
"""

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

# Path resolution — single source of truth, shared with the SDK
from .core.paths import PROJECT_ROOT, DEMO_DIR, MAIN_PY


# ---------------------------------------------------------------------------
# Safe Execution Wrapper
# ---------------------------------------------------------------------------

def _run_safely(cmd: list, timeout: int = 300) -> tuple:
    """
    Run a subprocess with safe error handling.
    Returns (success: bool, stdout: str, stderr: str).
    Never raises — always returns gracefully.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Workflow timed out after {timeout} seconds"
    except FileNotFoundError as e:
        return False, "", f"Executable not found: {e}"
    except Exception as e:
        return False, "", f"Unexpected error: {e}"


def _print_result(success: bool, workflow: str, output_dir: str, stderr: str = "") -> None:
    """Print a user-friendly result summary."""
    print()
    if success:
        print(f"✅ {workflow.title()} workflow completed successfully")
        print(f"   Output: {output_dir}/")
    else:
        print(f"❌ {workflow.title()} workflow failed")
        if stderr:
            # Only show last 3 lines of stderr to avoid wall of text
            lines = stderr.strip().split("\n")
            snippet = "\n".join(lines[-3:]) if len(lines) > 3 else stderr
            print(f"   Error: {snippet}")
    print()


# ---------------------------------------------------------------------------
# Demo Runners
# ---------------------------------------------------------------------------

def run_literature_demo(args):
    """Run the literature review demo with safe execution."""
    out_dir = args.output_dir or "outputs/literature"
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable,
        str(DEMO_DIR / "demo_literature_review.py"),
        "--topic", args.query,
        "--output-dir", out_dir,
    ]
    if args.max_results:
        cmd.extend(["--max_results", str(args.max_results)])
    if args.use_mock:
        cmd.append("--use_mock")

    success, stdout, stderr = _run_safely(cmd)
    print(stdout, end="")
    _print_result(success, "literature", out_dir, stderr)
    return success


def run_biomarker_demo(args):
    """Run the biomarker discovery demo with safe execution."""
    out_dir = args.output_dir or "outputs/biomarker"
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable,
        str(DEMO_DIR / "demo_biomarker_discovery.py"),
        "--disease", args.disease,
        "--output-dir", out_dir,
    ]
    if args.geo_id:
        cmd.extend(["--geo_id", args.geo_id])
    if args.alpha:
        cmd.extend(["--alpha", str(args.alpha)])
    if args.use_synthetic:
        cmd.append("--use_synthetic")

    success, stdout, stderr = _run_safely(cmd)
    print(stdout, end="")
    _print_result(success, "biomarker", out_dir, stderr)
    return success


def run_causal_demo(args):
    """Run the causal inference (MR) demo with safe execution."""
    out_dir = args.output_dir or "outputs/causal"
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable,
        str(DEMO_DIR / "demo_causal_inference.py"),
        "--exposure", args.exposure,
        "--outcome", args.outcome,
        "--output-dir", out_dir,
    ]
    if args.n_snps:
        cmd.extend(["--n_snps", str(args.n_snps)])
    if args.seed:
        cmd.extend(["--seed", str(args.seed)])

    success, stdout, stderr = _run_safely(cmd)
    print(stdout, end="")
    _print_result(success, "causal", out_dir, stderr)
    return success


def run_main_pipeline(args):
    """Run the full research lifecycle pipeline."""
    cmd = [sys.executable, str(MAIN_PY)]
    if args.question:
        cmd.extend(["--question", args.question])
    if args.workflow:
        cmd.extend(["--workflow", args.workflow])
    if args.stage:
        cmd.extend(["--stage", args.stage])
    if args.mock:
        cmd.append("--mock")
    if args.output:
        cmd.extend(["--output", args.output])

    success, stdout, stderr = _run_safely(cmd)
    print(stdout, end="")
    if not success:
        print(f"❌ Pipeline failed: {stderr}")
    return success


# ---------------------------------------------------------------------------
# Doctor Command
# ---------------------------------------------------------------------------

def run_doctor():
    """Check environment health and report status."""
    print("=" * 60)
    print("BioResearch Agent Framework — Environment Health Check")
    print("=" * 60)

    checks = []

    # 1. Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 9)
    checks.append(("Python >= 3.9", py_ok, f"{py_version.major}.{py_version.minor}.{py_version.micro}"))

    # 2. Core dependencies (REQUIRED — failure here blocks all_ok)
    deps = ["numpy", "pandas", "scipy", "matplotlib", "requests", "yaml"]
    for dep in deps:
        try:
            importlib.import_module(dep)
            checks.append((f"Package: {dep}", True, "installed"))
        except ImportError:
            checks.append((f"Package: {dep}", False, "NOT FOUND — run: pip install -r requirements.txt"))

    # 3. networkx (REQUIRED — the literature knowledge-graph figure depends on it)
    try:
        importlib.import_module("networkx")
        checks.append(("Package: networkx", True, "installed (knowledge-graph figure)"))
    except ImportError:
        checks.append(("Package: networkx", False, "NOT FOUND — run: pip install -e ."))

    # 4. Demo files exist (REQUIRED)
    for demo in ["literature", "biomarker", "causal"]:
        demo_file = DEMO_DIR / f"demo_{demo}_review.py" if demo == "literature" else \
                    DEMO_DIR / f"demo_{demo}_discovery.py" if demo == "biomarker" else \
                    DEMO_DIR / f"demo_{demo}_inference.py"
        checks.append((f"Demo: {demo}", demo_file.exists(), str(demo_file)))

    # 5. Output directory writable (REQUIRED)
    test_dir = PROJECT_ROOT / "outputs"
    try:
        test_dir.mkdir(exist_ok=True)
        checks.append(("Output directory", True, str(test_dir)))
    except Exception as e:
        checks.append(("Output directory", False, str(e)))

    # 6. Network connectivity (WARNING ONLY — does not block all_ok)
    try:
        import socket
        socket.create_connection(("eutils.ncbi.nlm.nih.gov", 443), timeout=5)
        checks.append(("Network (PubMed)", True, "reachable"))
    except Exception:
        checks.append(("Network (PubMed)", None, "unreachable — demos will use synthetic fallbacks"))  # None = warning

    # Print results
    print()
    all_ok = True
    for name, ok, detail in checks:
        if ok is True:
            status = "✅"
        elif ok is False:
            status = "❌"
        else:  # None = warning
            status = "⚠️"
        print(f"  {status} {name:30s} {detail}")
        if ok is False:
            all_ok = False

    print()
    if all_ok:
        print("🟢 All checks passed. Ready to run workflows.")
    else:
        print("🟡 Some critical checks failed. See ❌ items above.")
    print("=" * 60)
    return all_ok


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="bioresearch",
        description="BioResearch Agent Framework — Run biomedical research workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  bioresearch run literature --query "microglia Alzheimer's disease"
  bioresearch run biomarker --disease "Parkinson's disease"
  bioresearch run causal --exposure BMI --outcome "Type 2 Diabetes"
  bioresearch doctor                    # Check environment health
  bioresearch --help
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run command ---
    run_parser = subparsers.add_parser("run", help="Run a workflow or demo")

    # Workflow type (optional — if omitted, runs full pipeline)
    run_parser.add_argument(
        "workflow_type",
        nargs="?",
        choices=["literature", "biomarker", "causal"],
        help="Pre-built demo workflow (optional)",
    )

    # Common args
    run_parser.add_argument("--output-dir", type=str, help="Output directory")
    run_parser.add_argument("--mock", action="store_true", default=True, help="Use mock/synthetic mode")

    # Literature review args
    run_parser.add_argument("--query", type=str, help="Research query (for literature workflow)")
    run_parser.add_argument("--max-results", type=int, dest="max_results", help="Max PubMed results")
    run_parser.add_argument("--use-mock", action="store_true", dest="use_mock", help="Force mock corpus")

    # Biomarker args
    run_parser.add_argument("--disease", type=str, help="Disease name (for biomarker workflow)")
    run_parser.add_argument("--geo-id", type=str, dest="geo_id", help="GEO dataset ID")
    run_parser.add_argument("--alpha", type=float, help="Significance threshold")
    run_parser.add_argument("--use-synthetic", action="store_true", dest="use_synthetic", help="Force synthetic data")

    # Causal args
    run_parser.add_argument("--exposure", type=str, help="Exposure trait (for causal workflow)")
    run_parser.add_argument("--outcome", type=str, help="Outcome trait (for causal workflow)")
    run_parser.add_argument("--n-snps", type=int, dest="n_snps", help="Number of SNPs to simulate")
    run_parser.add_argument("--seed", type=int, help="Random seed")

    # Full pipeline args
    run_parser.add_argument("--question", type=str, help="Research question (for full pipeline)")
    run_parser.add_argument("--workflow", type=str, choices=["full", "discovery", "mechanism", "clinical", "methodology", "review", "grant"], help="Workflow template")
    run_parser.add_argument("--stage", type=str, help="Run up to this stage")
    run_parser.add_argument("--output", type=str, default="output.json", help="Output file")

    # --- doctor command ---
    doctor_parser = subparsers.add_parser("doctor", help="Check environment health")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "doctor":
        ok = run_doctor()
        sys.exit(0 if ok else 1)

    if args.command != "run":
        parser.print_help()
        sys.exit(1)

    # Dispatch to appropriate handler
    if args.workflow_type == "literature":
        if not args.query:
            print("Error: --query is required for literature workflow")
            sys.exit(1)
        success = run_literature_demo(args)
    elif args.workflow_type == "biomarker":
        if not args.disease:
            print("Error: --disease is required for biomarker workflow")
            sys.exit(1)
        success = run_biomarker_demo(args)
    elif args.workflow_type == "causal":
        if not args.exposure or not args.outcome:
            print("Error: --exposure and --outcome are required for causal workflow")
            sys.exit(1)
        success = run_causal_demo(args)
    else:
        # Full pipeline mode
        if not args.question:
            print("Error: --question is required (or specify a workflow_type: literature/biomarker/causal)")
            sys.exit(1)
        success = run_main_pipeline(args)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
