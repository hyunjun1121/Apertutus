#!/usr/bin/env python3
"""
Add MHJ metadata (base_prompt, num_turns) and violation categories to evaluation results
Matches entries using first turn's original_content
"""

import json
from pathlib import Path

def add_metadata_and_categories():
    print("="*60)
    print("ADDING MHJ METADATA AND CATEGORIES TO EVALUATION RESULTS")
    print("="*60)

    # Load original MHJ dataset
    print("\nLoading original MHJ dataset...")
    with open('mhj_dataset.json', 'r', encoding='utf-8') as f:
        mhj_dataset = json.load(f)

    # Create lookup dictionary based on first turn content
    print("Creating lookup dictionary...")
    mhj_lookup = {}
    for entry in mhj_dataset:
        if entry['turns'] and len(entry['turns']) > 0:
            first_turn = entry['turns'][0].get('content', '')
            if first_turn:
                mhj_lookup[first_turn] = {
                    'base_prompt': entry.get('base_prompt', ''),
                    'num_turns': entry.get('num_turns', 0),
                    'turn_type': entry.get('turn_type', ''),
                    'source': entry.get('source', 'MHJ')
                }

    print(f"Created lookup with {len(mhj_lookup)} entries")

    # Load base prompt classifications
    print("\nLoading base prompt classifications...")
    with open('base_prompt_classifications.json', 'r', encoding='utf-8') as f:
        classifications = json.load(f)

    print(f"Loaded {len(classifications)} classifications")

    # Process all evaluation files
    eval_dir = Path('evaluation_results')
    eval_files = list(eval_dir.glob('*_evaluated.json'))

    print(f"\nFound {len(eval_files)} evaluation files to update")

    for eval_file in eval_files:
        print(f"\nProcessing {eval_file.name}...")

        with open(eval_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated = 0
        metadata_added = 0
        categories_added = 0

        for entry in data:
            # Try to find original_content from first turn
            original_content = None

            # Check if turns exist and have original_content
            if entry.get('turns') and len(entry['turns']) > 0:
                # Look for turn_number 1 or first turn
                for turn in entry['turns']:
                    if turn.get('turn_number', 0) == 1 or entry['turns'].index(turn) == 0:
                        # Check for original_content field
                        if 'original_content' in turn:
                            original_content = turn['original_content']
                        elif 'content' in turn:
                            # Fallback to content if original_content doesn't exist
                            original_content = turn['content']
                        break

            # Match with MHJ dataset using original_content
            if original_content and original_content in mhj_lookup:
                mhj_info = mhj_lookup[original_content]

                # Add MHJ metadata
                if 'base_prompt' not in entry:
                    entry['base_prompt'] = mhj_info['base_prompt']
                    entry['num_turns'] = mhj_info['num_turns']
                    entry['turn_type'] = mhj_info['turn_type']
                    entry['source'] = mhj_info['source']
                    metadata_added += 1

                # Add violation category
                base_prompt = entry['base_prompt']
                if base_prompt in classifications and 'violation_category' not in entry:
                    entry['violation_category'] = classifications[base_prompt]['category']
                    entry['category_reasoning'] = classifications[base_prompt]['reasoning']
                    categories_added += 1

                updated += 1
            else:
                # Try fallback method using entry_index
                if 'entry_index' in entry and entry['entry_index'] < len(mhj_dataset):
                    mhj_entry = mhj_dataset[entry['entry_index']]

                    if 'base_prompt' not in entry:
                        entry['base_prompt'] = mhj_entry.get('base_prompt', '')
                        entry['num_turns'] = mhj_entry.get('num_turns', 0)
                        entry['turn_type'] = mhj_entry.get('turn_type', '')
                        entry['source'] = mhj_entry.get('source', 'MHJ')
                        metadata_added += 1

                    # Add violation category
                    base_prompt = entry.get('base_prompt', '')
                    if base_prompt and base_prompt in classifications and 'violation_category' not in entry:
                        entry['violation_category'] = classifications[base_prompt]['category']
                        entry['category_reasoning'] = classifications[base_prompt]['reasoning']
                        categories_added += 1

                    updated += 1

        # Save updated file with new name
        output_file = eval_dir / f"{eval_file.stem}_with_metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Updated {updated} entries")
        print(f"  Added metadata to {metadata_added} entries")
        print(f"  Added categories to {categories_added} entries")
        print(f"  Saved to: {output_file.name}")

    # Generate summary statistics
    print("\n" + "="*60)
    print("GENERATING SUMMARY STATISTICS")
    print("="*60)

    all_stats = {}
    category_distribution = {}

    for eval_file in eval_dir.glob('*_with_metadata.json'):
        with open(eval_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        lang = eval_file.stem.replace('_evaluated_with_metadata', '')

        # Count statistics
        refused = sum(1 for d in data if d.get('evaluation', {}).get('refused', 0) == 1)

        # Category distribution for this language
        lang_categories = {}
        for entry in data:
            cat = entry.get('violation_category', 'Unknown')
            lang_categories[cat] = lang_categories.get(cat, 0) + 1
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        all_stats[lang] = {
            'total_entries': len(data),
            'refused_count': refused,
            'refusal_rate': (refused / len(data) * 100) if data else 0,
            'category_breakdown': lang_categories
        }

    # Save comprehensive summary
    summary = {
        'total_languages': len(all_stats),
        'total_entries': sum(s['total_entries'] for s in all_stats.values()),
        'language_stats': all_stats,
        'overall_category_distribution': category_distribution
    }

    summary_file = eval_dir / 'complete_evaluation_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved comprehensive summary to: {summary_file}")

    # Print category distribution
    print("\nOVERALL CATEGORY DISTRIBUTION:")
    sorted_cats = sorted(category_distribution.items(), key=lambda x: x[1], reverse=True)
    for cat, count in sorted_cats:
        percentage = (count / summary['total_entries']) * 100
        print(f"  {cat:35s}: {count:4d} ({percentage:5.1f}%)")

    print("\n" + "="*60)
    print("COMPLETE!")
    print(f"Updated {len(eval_files)} evaluation files with metadata and categories")
    print("="*60)


if __name__ == "__main__":
    add_metadata_and_categories()