import pandas as pd
import json

# Read Excel file
df = pd.read_excel(r'E:\Project\Apertutus\mhj_dataset.xlsx')
print(f'Loaded {len(df)} rows from Excel file')

# Convert to list of dictionaries
result = []

for index, row in df.iterrows():
    # Parse the jailbreak_turns JSON string
    try:
        turns_data = json.loads(row['jailbreak_turns'])
    except json.JSONDecodeError as e:
        print(f"Error parsing row {index}: {e}")
        continue

    # Create entry with individual turns
    entry = {
        'source': row['source'],
        'base_prompt': row['base_prompt'],
        'turn_type': row['turn_type'],
        'num_turns': row['num_turns'],
        'turns': []
    }

    # Extract individual turns
    for turn_key in sorted(turns_data.keys()):
        if turn_key.startswith('turn_'):
            turn_number = int(turn_key.split('_')[1])
            entry['turns'].append({
                'turn_number': turn_number,
                'content': turns_data[turn_key]
            })

    result.append(entry)

# Save to JSON file
output_path = r'E:\Project\Apertutus\mhj_dataset.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f'Successfully converted {len(result)} entries to JSON')
print(f'Saved to: {output_path}')

# Show sample of first entry
if result:
    print('\nSample of first entry:')
    sample = result[0].copy()
    if 'turns' in sample and len(sample['turns']) > 2:
        sample['turns'] = sample['turns'][:2] + [{'...': 'more turns'}]
    print(json.dumps(sample, indent=2, ensure_ascii=False))