"""
Example: Biomarker Discovery
Demonstrates how to use ResearchOS for a biomarker discovery workflow.
"""

from research_os.core.runtime import ResearchRuntime

runtime = ResearchRuntime()

query = """
Identify biomarkers for a neurodegenerative condition using single-cell RNA-seq.
Focus on immune-related cell types and prioritize candidates with multi-modal evidence.
"""

result = runtime.run(query)

print("=== ResearchOS Output ===")
print(result)
