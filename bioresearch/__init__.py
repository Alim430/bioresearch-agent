"""
BioResearch Agent Framework — SDK

Programmatic interface to all research workflows.

Usage:
    from bioresearch import Agent

    agent = Agent()
    result = agent.run(
        workflow="literature",
        query="microglia Alzheimer's disease",
        output_dir="outputs/literature"
    )
    print(result.report_path)
    print(result.figures)
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class AgentResult:
    """Result container for a workflow execution."""
    workflow: str
    output_dir: str
    success: bool = False
    report_path: Optional[str] = None
    figures: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<AgentResult {status} workflow={self.workflow} output={self.output_dir}>"


class Agent:
    """
    BioResearch Agent SDK.

    Executes biomedical research workflows programmatically.
    """

    def __init__(self, llm: str = "mock"):
        self.llm = llm

    def run(self, workflow: str, output_dir: Optional[str] = None, **kwargs) -> AgentResult:
        """
        Execute a research workflow via the CLI (same path as CLI users).

        Args:
            workflow: One of "literature", "biomarker", "causal"
            output_dir: Directory for outputs (default: outputs/{workflow}/)
            **kwargs: Workflow-specific parameters

        Returns:
            AgentResult with output paths and success status
        """
        if workflow not in ("literature", "biomarker", "causal"):
            raise ValueError(f"Unknown workflow: {workflow}. Choose: literature, biomarker, causal")

        if output_dir is None:
            output_dir = f"outputs/{workflow}"

        os.makedirs(output_dir, exist_ok=True)

        # Build CLI command (same as user would run)
        cmd = ["bioresearch", "run", workflow, "--output-dir", output_dir]

        # Map kwargs to CLI args
        arg_map = {
            "query": "--query",
            "disease": "--disease",
            "geo_id": "--geo-id",
            "alpha": "--alpha",
            "exposure": "--exposure",
            "outcome": "--outcome",
            "n_snps": "--n-snps",
            "seed": "--seed",
            "max_results": "--max-results",
        }

        for key, value in kwargs.items():
            if key in arg_map and value is not None:
                cmd.extend([arg_map[key], str(value)])
            elif key == "use_mock" and value:
                cmd.append("--use-mock")
            elif key == "use_synthetic" and value:
                cmd.append("--use-synthetic")

        # Delegate to the CLI's safe executor — identical execution path AND error handling
        from .cli import _run_safely

        success, stdout, stderr = _run_safely(cmd)
        if not success:
            error = f"Command: {' '.join(cmd)}\nSTDERR:\n{stderr}\nSTDOUT:\n{stdout}"
        else:
            error = None

        # Discover outputs
        figures = []
        tables = []
        report_path = None

        if success and Path(output_dir).exists():
            for f in Path(output_dir).iterdir():
                if f.suffix in (".png", ".jpg", ".svg"):
                    figures.append(str(f))
                elif f.suffix in (".csv", ".tsv"):
                    tables.append(str(f))
                elif f.suffix in (".md", ".txt") and ("report" in f.name or "interpretation" in f.name or "outline" in f.name or "gaps" in f.name):
                    report_path = str(f)

        return AgentResult(
            workflow=workflow,
            output_dir=output_dir,
            success=success,
            report_path=report_path,
            figures=figures,
            tables=tables,
            error=error,
        )

    def __repr__(self):
        return f"<BioResearchAgent llm={self.llm}>"
