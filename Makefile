# BioResearch Agent Framework — Quick Commands
.PHONY: help install demo-lit demo-bio demo-causal clean test-cli

PYTHON := python3

help:
	@echo "BioResearch Agent Framework — Quick Commands"
	@echo ""
	@echo "  make install       Install package in editable mode"
	@echo "  make demo-lit      Run literature review demo"
	@echo "  make demo-bio      Run biomarker discovery demo"
	@echo "  make demo-causal   Run causal inference (MR) demo"
	@echo "  make test-cli      Test CLI commands"
	@echo "  make clean         Remove generated outputs"

install:
	$(PYTHON) -m pip install -e .

demo-lit: install
	@mkdir -p outputs/literature
	bioresearch run literature \
		--query "microglia Alzheimer's disease" \
		--output-dir outputs/literature
	@echo "✓ Literature review complete. See outputs/literature/"

demo-bio: install
	@mkdir -p outputs/biomarker
	bioresearch run biomarker \
		--disease "Parkinson's disease" \
		--output-dir outputs/biomarker
	@echo "✓ Biomarker discovery complete. See outputs/biomarker/"

demo-causal: install
	@mkdir -p outputs/causal
	bioresearch run causal \
		--exposure "BMI" --outcome "Type 2 Diabetes" \
		--output-dir outputs/causal
	@echo "✓ Causal inference complete. See outputs/causal/"

test-cli: install
	@echo "Testing bioresearch CLI..."
	bioresearch --help
	@echo ""
	@echo "Testing bioresearch run --help..."
	bioresearch run --help
	@echo ""
	@echo "✓ CLI test complete"

clean:
	rm -rf outputs/
	@echo "✓ Cleaned all demo outputs"
