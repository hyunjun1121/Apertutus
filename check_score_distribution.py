#!/usr/bin/env python3
"""
Check the distribution of evaluation scores
"""

import json
import numpy as np
from pathlib import Path

def check_scores():
    eval_dir = Path('evaluation_results')

    # Check all evaluated files
    files_to_check = list(eval_dir.glob('*_evaluated_with_metadata.json'))

    print("="*60)
    print("CHECKING EVALUATION SCORE DISTRIBUTIONS")
    print("="*60)

    all_convincing = []
    all_specific = []
    all_refused = []

    for file_path in files_to_check[:3]:  # Check first 3 languages
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        language = file_path.stem.split('_')[0]

        # Collect scores
        refused_list = []
        convincing_list = []
        specific_list = []

        for entry in data:
            eval_data = entry.get('evaluation', {})
            refused = eval_data.get('refused', 0)
            convincing = eval_data.get('convincing_score', 0)
            specific = eval_data.get('specific_score', 0)

            refused_list.append(refused)
            convincing_list.append(convincing)
            specific_list.append(specific)

            all_refused.append(refused)
            all_convincing.append(convincing)
            all_specific.append(specific)

        # Calculate distributions
        print(f"\n{language}:")
        print(f"  Total entries: {len(data)}")

        # Refused distribution
        refused_values, refused_counts = np.unique(refused_list, return_counts=True)
        print(f"\n  Refused distribution:")
        for val, count in zip(refused_values, refused_counts):
            print(f"    {val}: {count} ({count/len(data)*100:.1f}%)")

        # Convincing distribution
        conv_values, conv_counts = np.unique(convincing_list, return_counts=True)
        print(f"\n  Convincing score distribution:")
        for val, count in zip(conv_values, conv_counts):
            print(f"    {val}: {count} ({count/len(data)*100:.1f}%)")

        # Specific distribution
        spec_values, spec_counts = np.unique(specific_list, return_counts=True)
        print(f"\n  Specific score distribution:")
        for val, count in zip(spec_values, spec_counts):
            print(f"    {val}: {count} ({count/len(data)*100:.1f}%)")

        # Show examples of entries with refused=1
        print(f"\n  Examples of REFUSED entries:")
        refused_count = 0
        for i, entry in enumerate(data):
            if entry.get('evaluation', {}).get('refused', 0) == 1:
                prompt = entry.get('base_prompt', '')[:50]
                print(f"    Entry {i}: {prompt}...")
                refused_count += 1
                if refused_count >= 3:
                    break

        # Show examples of entries with high scores
        print(f"\n  Examples of HIGH SCORE entries (conv or spec > 3):")
        high_count = 0
        for i, entry in enumerate(data):
            eval_data = entry.get('evaluation', {})
            conv = eval_data.get('convincing_score', 0)
            spec = eval_data.get('specific_score', 0)
            if conv > 3 or spec > 3:
                prompt = entry.get('base_prompt', '')[:50]
                print(f"    Entry {i}: conv={conv}, spec={spec} | {prompt}...")
                high_count += 1
                if high_count >= 3:
                    break

        if high_count == 0:
            print("    No entries with scores > 3 found!")

    # Overall statistics
    print("\n" + "="*60)
    print("OVERALL STATISTICS (3 languages)")
    print("="*60)

    print(f"\nTotal entries analyzed: {len(all_convincing)}")

    print(f"\nConvincing scores:")
    conv_values, conv_counts = np.unique(all_convincing, return_counts=True)
    for val, count in zip(conv_values, conv_counts):
        print(f"  {val}: {count} ({count/len(all_convincing)*100:.1f}%)")

    print(f"\nSpecific scores:")
    spec_values, spec_counts = np.unique(all_specific, return_counts=True)
    for val, count in zip(spec_values, spec_counts):
        print(f"  {val}: {count} ({count/len(all_specific)*100:.1f}%)")

    print(f"\nRefused:")
    ref_values, ref_counts = np.unique(all_refused, return_counts=True)
    for val, count in zip(ref_values, ref_counts):
        print(f"  {val}: {count} ({count/len(all_refused)*100:.1f}%)")

if __name__ == "__main__":
    check_scores()