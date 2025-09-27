#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Load evaluation results
base_eval = Path("evaluation_results_20250926_210855/base_model_eval.json")
finetuned_eval = Path("evaluation_results_20250926_210855/finetuned_model_eval.json")

print("Comparison placeholder")
print("Will compare:")
print(f"  - Base: {base_eval}")
print(f"  - Fine-tuned: {finetuned_eval}")

# TODO: Create comparison visualizations and report
# Metrics to compare:
# - Refusal rate
# - Convincing score distribution
# - Specific score distribution
# - Per-language breakdown
