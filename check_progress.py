#!/usr/bin/env python3
"""
Check translation progress
"""

import os
import subprocess
import json
import glob

def check_progress():
    """Check and display translation progress"""

    print("="*60)
    print("TRANSLATION PROGRESS")
    print("="*60)
    print()

    # Check active tmux sessions
    result = subprocess.run("tmux ls 2>/dev/null | grep trans_", shell=True, capture_output=True, text=True)
    active_sessions = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

    print(f"Active tmux sessions: {active_sessions}")
    print()

    # Load language list
    with open('config.json', 'r') as f:
        config = json.load(f)
    languages = [lang['code'] for lang in config['languages']]

    # Check completed parts
    output_dir = "multilingual_datasets"
    os.makedirs(output_dir, exist_ok=True)

    print("Progress by language:")
    print("-" * 40)

    total_parts = 0
    completed_languages = []

    for lang in languages:
        # Find part files
        part_pattern = f"{output_dir}/mhj_dataset_{lang}_part*.json"
        part_files = glob.glob(part_pattern)

        # Check if merged file exists
        merged_file = f"{output_dir}/mhj_dataset_{lang}.json"
        has_merged = os.path.exists(merged_file)

        if part_files or has_merged:
            status = "✓ MERGED" if has_merged else f"{len(part_files)} parts"
            print(f"  {lang:15} : {status}")
            total_parts += len(part_files)

            if has_merged:
                completed_languages.append(lang)

    print()
    print("-" * 40)
    print(f"Total part files: {total_parts}")
    print(f"Completed (merged): {len(completed_languages)}/{len(languages)} languages")

    if active_sessions > 0:
        print()
        print("Sessions still running. To view a session:")
        print("  tmux attach -t <session_name>")
        print("  (Exit with Ctrl+B, then D)")

    # Estimate completion
    if active_sessions > 0:
        print()
        print("Estimated completion:")
        total_expected = len(languages) * 6  # ~6 parts per language (537/100)
        completed_percentage = (total_parts / total_expected) * 100 if total_expected > 0 else 0
        print(f"  Progress: {completed_percentage:.1f}%")

if __name__ == "__main__":
    check_progress()