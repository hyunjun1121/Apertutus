#!/usr/bin/env python3
"""
Complete Safety Fine-tuning Experiment for Apertus-70B
Integrates dataset preparation, LoRA fine-tuning, and evaluation
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
import time

class SafetyExperimentRunner:
    def __init__(self):
        self.experiment_dir = Path("experiment_datasets")
        self.finetuning_dir = Path("finetuning_datasets")
        self.results_dir = Path("evaluation_results")
        self.results_dir.mkdir(exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_command(self, cmd, description):
        """Run a command and display progress"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {description}")
        print(f"{'='*60}")
        print(f"Command: {cmd}")

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            return False
        else:
            print(result.stdout)
            return True

    def phase1_data_preparation(self):
        """Phase 1: Split and prepare datasets"""
        print("\n" + "="*70)
        print("PHASE 1: DATA PREPARATION")
        print("="*70)

        # Step 1: Split dataset
        if not self.run_command(
            "python3 split_dataset_for_evaluation.py --action split",
            "Splitting dataset into train/test (80/20)"
        ):
            return False

        # Step 2: Verify no overlap
        if not self.run_command(
            "python3 split_dataset_for_evaluation.py --action verify",
            "Verifying train/test separation"
        ):
            return False

        # Step 3: Prepare fine-tuning dataset
        if not self.run_command(
            "python3 split_dataset_for_evaluation.py --action prepare",
            "Preparing fine-tuning dataset from train split"
        ):
            return False

        print("\nPhase 1 complete: Datasets prepared")
        return True

    def phase2_lora_finetuning(self):
        """Phase 2: Run LoRA fine-tuning with Apertus"""
        print("\n" + "="*70)
        print("PHASE 2: LORA FINE-TUNING")
        print("="*70)

        # Run the Apertus fine-tuning script
        if not self.run_command(
            "python3 run_apertus_safety_finetuning.py",
            "Setting up Apertus LoRA fine-tuning"
        ):
            return False

        # Find the generated launch script
        launch_scripts = list(Path(".").glob("launch_safety_finetuning_*.sh"))
        if not launch_scripts:
            print("ERROR: No launch script found")
            return False

        latest_script = sorted(launch_scripts)[-1]

        print(f"\nLaunch script created: {latest_script}")
        print("\nIMPORTANT: Fine-tuning must be run on a GPU server with:")
        print("  - Apertus model access")
        print("  - Swiss AI API credentials")
        print("  - Sufficient GPU memory (70B model)")
        print(f"\nTo start fine-tuning, run: ./{latest_script}")

        # Store the adapter path for later use
        self.adapter_path = f"safety_lora_adapter_{self.timestamp}"

        return True

    def phase3_generate_responses(self):
        """Phase 3: Generate responses on test set"""
        print("\n" + "="*70)
        print("PHASE 3: GENERATE TEST RESPONSES")
        print("="*70)

        test_dir = self.experiment_dir / "test"

        # Create response generation script for test set
        response_script = f"""#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

# Configuration
test_dir = Path("{test_dir}")
output_dir = Path("test_responses_{self.timestamp}")
output_dir.mkdir(exist_ok=True)

# Load test files
test_files = list(test_dir.glob("*.json"))
print(f"Found {{len(test_files)}} test files")

# TODO: Add actual response generation using:
# 1. Base Apertus-70B model
# 2. Fine-tuned Apertus-70B + LoRA adapter

print("Response generation placeholder")
print("This requires Apertus API access")
"""

        script_path = f"generate_test_responses_{self.timestamp}.py"
        with open(script_path, 'w') as f:
            f.write(response_script)

        print(f"Response generation script created: {script_path}")
        print("NOTE: Actual response generation requires Apertus API access")

        return True

    def phase4_evaluation(self):
        """Phase 4: Run StrongReject evaluation"""
        print("\n" + "="*70)
        print("PHASE 4: STRONGREJECT EVALUATION")
        print("="*70)

        eval_script = f"""#!/usr/bin/env python3
import json
from pathlib import Path

# Paths
base_responses = Path("test_responses_{self.timestamp}/base_model")
finetuned_responses = Path("test_responses_{self.timestamp}/finetuned_model")
output_dir = Path("evaluation_results_{self.timestamp}")
output_dir.mkdir(exist_ok=True)

print("Evaluation placeholder")
print("Will evaluate:")
print(f"  - Base model: {{base_responses}}")
print(f"  - Fine-tuned: {{finetuned_responses}}")
print(f"  - Output: {{output_dir}}")

# TODO: Run StrongReject evaluation using run_strongreject_parallel.py
"""

        script_path = f"evaluate_models_{self.timestamp}.py"
        with open(script_path, 'w') as f:
            f.write(eval_script)

        print(f"Evaluation script created: {script_path}")

        return True

    def phase5_comparison(self):
        """Phase 5: Compare results"""
        print("\n" + "="*70)
        print("PHASE 5: RESULTS COMPARISON")
        print("="*70)

        comparison_script = f"""#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Load evaluation results
base_eval = Path("evaluation_results_{self.timestamp}/base_model_eval.json")
finetuned_eval = Path("evaluation_results_{self.timestamp}/finetuned_model_eval.json")

print("Comparison placeholder")
print("Will compare:")
print(f"  - Base: {{base_eval}}")
print(f"  - Fine-tuned: {{finetuned_eval}}")

# TODO: Create comparison visualizations and report
# Metrics to compare:
# - Refusal rate
# - Convincing score distribution
# - Specific score distribution
# - Per-language breakdown
"""

        script_path = f"compare_results_{self.timestamp}.py"
        with open(script_path, 'w') as f:
            f.write(comparison_script)

        print(f"Comparison script created: {script_path}")

        return True

    def generate_summary(self):
        """Generate experiment summary"""
        summary = {
            "timestamp": self.timestamp,
            "phases": {
                "1_data_preparation": "COMPLETE",
                "2_lora_finetuning": "READY (requires GPU)",
                "3_response_generation": "READY (requires API)",
                "4_evaluation": "READY",
                "5_comparison": "READY"
            },
            "datasets": {
                "train": str(self.experiment_dir / "train"),
                "test": str(self.experiment_dir / "test"),
                "finetuning": str(self.finetuning_dir)
            },
            "outputs": {
                "lora_adapter": self.adapter_path if hasattr(self, 'adapter_path') else None,
                "test_responses": f"test_responses_{self.timestamp}",
                "evaluation": f"evaluation_results_{self.timestamp}"
            },
            "next_steps": [
                "1. Run fine-tuning on GPU server",
                "2. Generate responses with both models",
                "3. Run StrongReject evaluation",
                "4. Compare and analyze results"
            ]
        }

        summary_file = f"experiment_summary_{self.timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")

        return summary

    def run(self):
        """Run complete experiment"""
        print("="*70)
        print("APERTUS-70B SAFETY FINE-TUNING EXPERIMENT")
        print(f"Started: {datetime.now()}")
        print("="*70)

        # Phase 1: Data preparation
        if not self.phase1_data_preparation():
            print("ERROR: Data preparation failed")
            return False

        # Phase 2: LoRA fine-tuning setup
        if not self.phase2_lora_finetuning():
            print("ERROR: Fine-tuning setup failed")
            return False

        # Phase 3: Response generation setup
        if not self.phase3_generate_responses():
            print("ERROR: Response generation setup failed")
            return False

        # Phase 4: Evaluation setup
        if not self.phase4_evaluation():
            print("ERROR: Evaluation setup failed")
            return False

        # Phase 5: Comparison setup
        if not self.phase5_comparison():
            print("ERROR: Comparison setup failed")
            return False

        # Generate summary
        summary = self.generate_summary()

        print("\n" + "="*70)
        print("EXPERIMENT SETUP COMPLETE")
        print("="*70)

        print("\nNext steps:")
        for step in summary["next_steps"]:
            print(f"  {step}")

        print(f"\nExperiment ID: {self.timestamp}")

        return True


def main():
    """Main entry point"""
    runner = SafetyExperimentRunner()

    success = runner.run()

    if success:
        print("\n✨ Experiment framework ready!")
        print("Follow the next steps to complete the evaluation.")
    else:
        print("\n❌ Experiment setup encountered errors.")
        print("Please check the error messages above.")

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())