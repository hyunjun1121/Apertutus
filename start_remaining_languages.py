#!/usr/bin/env python3
"""
Start tmux sessions for remaining languages only
"""

import os
import subprocess
import time
import json
from pathlib import Path

def get_remaining_languages():
    """Get list of languages that haven't been translated yet"""

    # Check which languages already exist in filtered directory
    filtered_dir = Path("multilingual_datasets_filtered")
    completed_files = list(filtered_dir.glob("mhj_dataset_*.json"))
    completed_languages = set()

    for file in completed_files:
        # Extract language code from filename
        # Format: mhj_dataset_LANG.json
        lang_code = file.stem.replace("mhj_dataset_", "")
        completed_languages.add(lang_code)

    print(f"Found {len(completed_languages)} completed languages:")
    for lang in sorted(completed_languages):
        print(f"  ✓ {lang}")

    # Get all languages from config
    with open('config.json', 'r') as f:
        config = json.load(f)

    all_languages = [lang['code'] for lang in config['languages']]

    # Find remaining languages
    remaining = [lang for lang in all_languages if lang not in completed_languages]

    print(f"\n{len(remaining)} languages remaining to translate:")
    for lang in remaining:
        print(f"  ○ {lang}")

    return remaining

def start_translation_sessions():
    """Start translation sessions for remaining languages only"""

    # Get remaining languages
    remaining_languages = get_remaining_languages()

    if not remaining_languages:
        print("\nAll languages have been translated!")
        return

    # Configuration
    ENTRIES_PER_SESSION = 100
    TOTAL_ENTRIES = 382  # Changed to 382 as per filtered dataset

    print("\n" + "="*60)
    print("STARTING TMUX SESSIONS FOR REMAINING LANGUAGES")
    print("="*60)
    print(f"Languages to translate: {len(remaining_languages)}")
    print(f"Entries per session: {ENTRIES_PER_SESSION}")
    print(f"Total entries per language: {TOTAL_ENTRIES}")
    print()

    # Kill existing translation sessions
    print("Cleaning up existing translation sessions...")
    subprocess.run("tmux ls 2>/dev/null | grep 'trans_' | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null",
                   shell=True)

    session_count = 0
    api_key_index = 0
    commands = []

    # Distribute languages evenly across API keys
    api_assignments = {}
    for i, lang in enumerate(remaining_languages):
        assigned_api = i % 5
        if assigned_api not in api_assignments:
            api_assignments[assigned_api] = []
        api_assignments[assigned_api].append(lang)

    print("\nAPI key assignments:")
    for api_idx, langs in api_assignments.items():
        print(f"  API key {api_idx}: {', '.join(langs[:3])}{'...' if len(langs) > 3 else ''} ({len(langs)} languages)")
    print()

    # Generate commands for each language
    for lang in remaining_languages:
        # Find which API key this language is assigned to
        assigned_api = next(api_idx for api_idx, langs in api_assignments.items() if lang in langs)

        for start in range(0, TOTAL_ENTRIES, ENTRIES_PER_SESSION):
            end = min(start + ENTRIES_PER_SESSION, TOTAL_ENTRIES)

            session_name = f"trans_{lang}_{start}"
            cmd = f"python3 tmux_batch_translator.py --language {lang} --start {start} --end {end} --api-key {assigned_api}"

            commands.append({
                'session': session_name,
                'cmd': cmd,
                'lang': lang,
                'range': f"{start}-{end}",
                'api_key': assigned_api
            })

            session_count += 1

    print(f"Will start {session_count} sessions total")
    print()

    # Execute in batches to avoid overwhelming
    batch_size = 10
    for i in range(0, len(commands), batch_size):
        batch = commands[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(commands) + batch_size - 1)//batch_size
        print(f"Starting batch {batch_num}/{total_batches}")

        for cmd_info in batch:
            tmux_cmd = f"tmux new-session -d -s '{cmd_info['session']}' '{cmd_info['cmd']}'"
            subprocess.run(tmux_cmd, shell=True)
            print(f"  Started {cmd_info['session']} (API key {cmd_info['api_key']})")

        time.sleep(1)  # Small delay between batches

    print()
    print("="*60)
    print(f"SUCCESS: Started {session_count} sessions for {len(remaining_languages)} languages")
    print("="*60)
    print()
    print("Monitor with:")
    print("  tmux ls | grep trans_ | wc -l    # Count active sessions")
    print("  tmux ls | head -20               # View first 20 sessions")
    print("  tmux attach -t SESSION_NAME      # View specific session")
    print()
    print("Check overall progress:")
    print("  python3 check_progress.py")
    print()
    print("Check specific language:")
    print("  ls multilingual_datasets/*.json | grep LANG_CODE")
    print()

    # Create monitoring script
    create_monitor_script(remaining_languages)

def create_monitor_script(languages):
    """Create a script to monitor progress"""

    script = """#!/bin/bash
echo "Translation Progress Monitor"
echo "============================"
echo ""
echo "Active sessions:"
tmux ls 2>/dev/null | grep trans_ | wc -l
echo ""
echo "Completed files by language:"
for lang in %s; do
    count=$(ls multilingual_datasets/mhj_dataset_${lang}_part*.json 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        echo "  $lang: $count parts completed"
    fi
done
echo ""
echo "Recently modified files (last 10):"
ls -lt multilingual_datasets/*.json 2>/dev/null | head -10
""" % ' '.join(languages)

    with open('monitor_remaining.sh', 'w') as f:
        f.write(script)

    os.chmod('monitor_remaining.sh', 0o755)
    print("Created monitor_remaining.sh for tracking progress")

if __name__ == "__main__":
    start_translation_sessions()