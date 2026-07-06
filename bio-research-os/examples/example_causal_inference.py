"""
Example: Causal Mechanism Inference
Demonstrates how to use ResearchOS for causal inference.
"""

from research_os.core.runtime import ResearchRuntime

runtime = ResearchRuntime()

query = """
What is the causal role of an immune-related module in microglia activation?
Use Mendelian randomization and perturbation evidence.
"""

result = runtime.run(query)

print("=== ResearchOS Output ===")
print(result)
