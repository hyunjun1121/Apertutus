#!/usr/bin/env python3
"""
Generate and execute all tmux commands efficiently
"""

import os
import subprocess
import time
import json

def start_translation_sessions():
    """Start all translation sessions efficiently"""

    # Configuration
    ENTRIES_PER_SESSION = 100
    TOTAL_ENTRIES = 537

    # Languages to translate (all 40)
    with open('config.json', 'r') as f:
        config = json.load(f)

    languages = [lang['code'] for lang in config['languages']]

    # Or use subset for testing
    # languages = ["kor.Hang", "jpn.Jpan", "fra.Latn", "deu.Latn", "spa.Latn"]

    print("="*60)
    print("STARTING ALL TMUX SESSIONS")
    print("="*60)
    print(f"Languages: {len(languages)}")
    print(f"Entries per session: {ENTRIES_PER_SESSION}")
    print(f"Total entries: {TOTAL_ENTRIES}")
    print()

    # Kill existing sessions
    print("Cleaning up existing sessions...")
    subprocess.run("tmux ls 2>/dev/null | grep 'trans_' | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null",
                   shell=True)

    session_count = 0
    api_key_index = 0
    commands = []

    # Generate all commands
    for lang in languages:
        for start in range(0, TOTAL_ENTRIES, ENTRIES_PER_SESSION):
            end = min(start + ENTRIES_PER_SESSION, TOTAL_ENTRIES)

            session_name = f"trans_{lang}_{start}"
            cmd = f"python tmux_batch_translator.py --language {lang} --start {start} --end {end} --api-key {api_key_index}"

            commands.append({
                'session': session_name,
                'cmd': cmd,
                'lang': lang,
                'range': f"{start}-{end}",
                'api_key': api_key_index
            })

            api_key_index = (api_key_index + 1) % 5
            session_count += 1

    print(f"Will start {session_count} sessions")
    print()

    # Execute in batches to avoid overwhelming
    batch_size = 10
    for i in range(0, len(commands), batch_size):
        batch = commands[i:i+batch_size]
        print(f"Starting batch {i//batch_size + 1}/{(len(commands) + batch_size - 1)//batch_size}")

        for cmd_info in batch:
            tmux_cmd = f"tmux new-session -d -s '{cmd_info['session']}' '{cmd_info['cmd']}'"
            subprocess.run(tmux_cmd, shell=True)
            print(f"  ✓ {cmd_info['session']} (API key {cmd_info['api_key']})")

        time.sleep(1)  # Small delay between batches

    print()
    print("="*60)
    print(f"SUCCESS: Started {session_count} sessions")
    print("="*60)
    print()
    print("Monitor with:")
    print("  tmux ls                      # List all sessions")
    print("  tmux ls | grep trans_ | wc -l  # Count active sessions")
    print("  tmux attach -t trans_kor.Hang_0  # View specific session")
    print()
    print("Check progress with:")
    print("  python check_progress.py")
    print()
    print("After completion, merge with:")
    print("  python merge_all.py")

if __name__ == "__main__":
    start_translation_sessions()