"""
BioResearch Agent Framework — Main Entry Point

Three-Layer Architecture:
    Research Lifecycle (12 Stages) → Research Engines (6) → Specialized Agents (23)

Usage:
    python main.py --question "Why does LRRK2 regulate neuroinflammation?"
    python main.py --question "Review microglia in Alzheimer's" --workflow review
    python main.py --stage literature --question "What biomarkers predict COVID-19 severity?"
    python main.py --demo literature
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent))

from core.router import Router
from core.state import Stage

DEMO_PATH = Path(__file__).parent / "demos"

def run_demo(demo_name: str):
    """Run one of the three built-in demos."""
    demos = {
        "literature": DEMO_PATH / "demo_literature_review.py",
        "biomarker": DEMO_PATH / "demo_biomarker_discovery.py",
        "causal": DEMO_PATH / "demo_causal_inference.py",
    }
    
    if demo_name not in demos:
        print(f"Available demos: {', '.join(demos.keys())}")
        return
    
    demo_file = demos[demo_name]
    if not demo_file.exists():
        print(f"Demo file not found: {demo_file}")
        return
    
    print(f"Running demo: {demo_name}")
    import subprocess
    subprocess.run([sys.executable, str(demo_file)])

def main():
    parser = argparse.ArgumentParser(
        description="BioResearch Agent Framework — 12-Stage Research Lifecycle"
    )
    parser.add_argument("--question", type=str, help="Research question")
    parser.add_argument("--workflow", type=str, default="full",
                       choices=["full", "discovery", "mechanism", "clinical",
                               "methodology", "review", "grant"],
                       help="Workflow template")
    parser.add_argument("--stage", type=str, default=None,
                       choices=[s.value for s in Stage if s != Stage.IDLE],
                       help="Run only up to this stage")
    parser.add_argument("--mock", action="store_true", default=True,
                       help="Use mock mode (synthetic data)")
    parser.add_argument("--max-iterations", type=int, default=10,
                       help="Max iterations")
    parser.add_argument("--output", type=str, default="output.json",
                       help="Output file")
    parser.add_argument("--demo", type=str, default=None,
                       choices=["literature", "biomarker", "causal"],
                       help="Run a built-in demo instead of main pipeline")
    
    args = parser.parse_args()
    
    # Run demo if requested
    if args.demo:
        run_demo(args.demo)
        return
    
    if not args.question:
        print("Error: --question is required (or use --demo)")
        parser.print_help()
        return
    
    router = Router(mock=args.mock)
    
    if args.stage:
        target = Stage(args.stage)
        state = router.run_stage(args.question, target)
    elif args.workflow and args.workflow != "full":
        state = router.run_workflow(args.question, args.workflow)
    else:
        state = router.run_full_lifecycle(args.question,
                                          max_iterations=args.max_iterations)
    
    # Output
    result = state.to_dict()
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"BioResearch Agent Framework — Execution Complete")
    print(f"{'='*60}")
    print(f"Question:     {state.question}")
    print(f"Final Stage:  {state.current_stage.value}")
    print(f"Hypotheses:   {result['n_hypotheses']}")
    print(f"Papers:       {result['n_papers']}")
    print(f"Evidence:     {result['n_evidence']}")
    print(f"Grade:        {result['overall_grade']}")
    print(f"Confidence:   {result['confidence_score']:.1f}%")
    print(f"Accept Prob:  {result['accept_probability']:.1%}")
    print(f"\nOutput:       {args.output}")
    
    if state.manuscript:
        print(f"\n--- Manuscript Preview ---")
        print(state.manuscript[:400] + "...")

if __name__ == "__main__":
    main()
