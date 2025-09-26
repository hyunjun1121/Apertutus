import json

with open('mhj_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

turn_dist = {}
for entry in data:
    turns = entry['num_turns']
    turn_dist[turns] = turn_dist.get(turns, 0) + 1

print("Turn distribution in original dataset:")
for turns in sorted(turn_dist.keys()):
    print(f"  {turns} turns: {turn_dist[turns]} entries")

total = len(data)
seven_plus = sum(v for k, v in turn_dist.items() if k >= 7)

print(f"\nTotal entries: {total}")
print(f"Entries with 7+ turns: {seven_plus} ({seven_plus/total*100:.1f}%)")
print(f"Entries to keep (1-6 turns): {total - seven_plus} ({(total-seven_plus)/total*100:.1f}%)")