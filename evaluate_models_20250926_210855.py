#!/usr/bin/env python3
import json
from pathlib import Path

# Paths
base_responses = Path("test_responses_20250926_210855/base_model")
finetuned_responses = Path("test_responses_20250926_210855/finetuned_model")
output_dir = Path("evaluation_results_20250926_210855")
output_dir.mkdir(exist_ok=True)

print("Evaluation placeholder")
print("Will evaluate:")
print(f"  - Base model: {base_responses}")
print(f"  - Fine-tuned: {finetuned_responses}")
print(f"  - Output: {output_dir}")

# TODO: Run StrongReject evaluation using run_strongreject_parallel.py
