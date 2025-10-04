import json
import glob
import os

# Find all _complete.json files
json_files = glob.glob("final_results/*_complete.json")

for json_file in json_files:
    print(f"Processing {json_file}...")

    # Read the JSON file
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ERROR: Failed to parse JSON - {e}")
        print(f"  Skipping {json_file}")
        continue

    # Filter entries where refused == 1
    refused_filtered = [entry for entry in data if entry.get('evaluation', {}).get('refused') == 1]
    print(f"  Found {len(refused_filtered)} entries with refused=1 out of {len(data)} total entries")

    # Filter entries where strongreject_score == 0.0
    strongreject_filtered = [entry for entry in data if entry.get('evaluation', {}).get('strongreject_score') == 0.0]
    print(f"  Found {len(strongreject_filtered)} entries with strongreject_score=0.0 out of {len(data)} total entries")

    base_name = os.path.basename(json_file)

    # Save refused=1 filtered data
    refused_name = base_name.replace('_complete.json', '_complete_refused_1.json')
    refused_path = os.path.join('final_results', refused_name)
    with open(refused_path, 'w', encoding='utf-8') as f:
        json.dump(refused_filtered, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {refused_path}")

    # Save strongreject_score=0.0 filtered data
    strongreject_name = base_name.replace('_complete.json', '_complete_strongreject_0.json')
    strongreject_path = os.path.join('final_results', strongreject_name)
    with open(strongreject_path, 'w', encoding='utf-8') as f:
        json.dump(strongreject_filtered, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {strongreject_path}")

print("\nAll files processed successfully!")
