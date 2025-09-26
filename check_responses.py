import json
from pathlib import Path

def check_response_files():
    response_dir = Path('llm_responses')
    files = sorted(response_dir.glob('mhj_dataset_*_with_responses.json'))

    print(f"Found {len(files)} response files")
    print("=" * 60)

    all_good = True

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        language = filepath.stem.split('_')[2]
        entry_count = len(data)

        # Count turns and errors
        total_turns = 0
        error_count = 0
        missing_response = 0

        for entry in data:
            turns = entry.get('turns', [])
            total_turns += len(turns)

            for turn in turns:
                if 'llm_response' not in turn:
                    missing_response += 1
                elif turn['llm_response'].startswith('ERROR:'):
                    error_count += 1

        # Check if complete
        status = "OK" if entry_count == 382 else "INCOMPLETE"
        if entry_count != 382:
            all_good = False

        print(f"[{status}] {language}: {entry_count}/382 entries, "
              f"{total_turns} turns, {error_count} errors, "
              f"{missing_response} missing")

    print("=" * 60)
    print(f"Overall: {'All files complete' if all_good else 'Some files incomplete'}")

    # Sample response check
    print("\n" + "=" * 60)
    print("Sample response structure (kor.Hang):")
    print("=" * 60)

    sample_file = response_dir / 'mhj_dataset_kor.Hang_with_responses.json'
    if sample_file.exists():
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data:
            first_entry = data[0]
            print(f"Entry 0:")
            print(f"  - entry_index: {first_entry.get('entry_index')}")
            print(f"  - turns: {len(first_entry.get('turns', []))}")

            first_turn = first_entry['turns'][0] if first_entry.get('turns') else {}
            if first_turn:
                print(f"\n  First turn:")
                print(f"    - content length: {len(first_turn.get('content', ''))}")
                print(f"    - llm_response length: {len(first_turn.get('llm_response', ''))}")
                print(f"    - response preview: {first_turn.get('llm_response', '')[:100]}...")

if __name__ == "__main__":
    check_response_files()