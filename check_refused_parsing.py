import json
import os
import re
from pathlib import Path

def extract_refused_from_raw(raw_response):
    """Extract refused value from raw response using regex patterns"""
    if not raw_response:
        return None

    # Pattern for #scores format: 1.b followed by value (this is the answer)
    pattern_scores_answer = r'1\.b\s+(\d+)'

    # Also check 1.a if it has a direct value
    pattern_scores_a = r'1\.a\s+(\d+)(?:\s|$)'

    # Pattern 1: "refused": value or "Refused": value
    pattern1 = r'"[Rr]efused"\s*:\s*(\d+)'

    # Pattern 2: Refused: value (without quotes)
    pattern2 = r'[Rr]efused\s*:\s*(\d+)'

    # Pattern 3: **Refused**: value
    pattern3 = r'\*\*[Rr]efused\*\*\s*:\s*(\d+)'

    # Pattern 4: - Refused: value (list format)
    pattern4 = r'-\s*[Rr]efused\s*:\s*(\d+)'

    # First priority: 1.b (the actual answer)
    patterns = [pattern_scores_answer, pattern_scores_a, pattern1, pattern2, pattern3, pattern4]

    for pattern in patterns:
        match = re.search(pattern, raw_response)
        if match:
            return int(match.group(1))

    return None

def check_json_file(filepath):
    """Check refused parsing in a single JSON file"""
    print(f"\nChecking: {os.path.basename(filepath)}")
    print("-" * 60)

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_entries = 0
    mismatches = []
    parsing_errors = []

    # Check if this is a list of entries
    if isinstance(data, list):
        for entry in data:
            if 'evaluation' in entry:
                total_entries += 1

                eval_data = entry['evaluation']
                raw_response = eval_data.get('raw_response', '')
                parsed_refused = eval_data.get('refused')
                extracted_refused = extract_refused_from_raw(raw_response)

                # Check for parsing issues
                if extracted_refused is None and parsed_refused is not None:
                    parsing_errors.append({
                        'entry_index': entry.get('entry_index', 'unknown'),
                        'parsed': parsed_refused,
                        'raw_snippet': raw_response[:200] if raw_response else 'No raw response'
                    })
                elif extracted_refused is not None and parsed_refused != extracted_refused:
                    mismatches.append({
                        'entry_index': entry.get('entry_index', 'unknown'),
                        'parsed': parsed_refused,
                        'extracted': extracted_refused,
                        'raw_snippet': raw_response[:200] if raw_response else 'No raw response'
                    })

    # Summary for this file
    print(f"Total entries checked: {total_entries}")
    print(f"Mismatches found: {len(mismatches)}")
    print(f"Parsing errors: {len(parsing_errors)}")

    if mismatches:
        print("\nMismatches (first 5):")
        for i, m in enumerate(mismatches[:5]):
            print(f"  {i+1}. Entry index: {m['entry_index']}")
            print(f"     Parsed: {m['parsed']}, Should be: {m['extracted']}")
            print(f"     Raw snippet: {m['raw_snippet'][:100]}...")

    if parsing_errors:
        print("\nParsing errors (first 5):")
        for i, e in enumerate(parsing_errors[:5]):
            print(f"  {i+1}. Entry index: {e['entry_index']}")
            print(f"     Parsed as: {e['parsed']}, but couldn't extract from raw")
            print(f"     Raw snippet: {e['raw_snippet'][:100]}...")

    return {
        'file': os.path.basename(filepath),
        'total': total_entries,
        'mismatches': len(mismatches),
        'errors': len(parsing_errors),
        'mismatch_details': mismatches,
        'error_details': parsing_errors
    }

def main():
    results_dir = Path("E:/Project/Apertutus/final_results")

    # Get all language JSON files (excluding summary files)
    json_files = [
        f for f in results_dir.glob("*.json")
        if "_complete.json" in f.name and not f.name.startswith("complete_")
    ]

    print(f"Found {len(json_files)} language result files to check")
    print("=" * 60)

    all_results = []

    for json_file in sorted(json_files):
        result = check_json_file(json_file)
        all_results.append(result)

    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)

    total_mismatches = sum(r['mismatches'] for r in all_results)
    total_errors = sum(r['errors'] for r in all_results)
    total_entries = sum(r['total'] for r in all_results)

    print(f"Total entries across all files: {total_entries}")
    print(f"Total mismatches: {total_mismatches}")
    print(f"Total parsing errors: {total_errors}")

    if total_mismatches > 0 or total_errors > 0:
        print("\nFiles with issues:")
        for r in all_results:
            if r['mismatches'] > 0 or r['errors'] > 0:
                print(f"  - {r['file']}: {r['mismatches']} mismatches, {r['errors']} errors")

if __name__ == "__main__":
    main()