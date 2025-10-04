import json

# Load translations
with open("strong_reject.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Translation Quality Verification\n")
print("=" * 80)

# Check each language
for lang_code in ["kor.Hang", "jpn.Jpan", "cmn.Hani", "arb.Arab", "deu.Latn", "fra.Latn"]:
    print(f"\n{lang_code}:")
    print("-" * 80)

    prompt = data[lang_code]["strongreject_prompt"]
    system = data[lang_code]["strongreject_system"]

    # Check placeholders
    has_forbidden = "{forbidden_prompt}" in prompt
    has_response = "{response}" in prompt

    print(f"Placeholder check:")
    print(f"  - {{forbidden_prompt}}: {'OK' if has_forbidden else 'MISSING'}")
    print(f"  - {{response}}: {'OK' if has_response else 'MISSING'}")

    # Check for unwanted markers
    unwanted = ["Translation:", "Explanation:", "Note:", "Remember:", "Output:", "Here is", "Below is the translation"]
    found_unwanted = []
    for marker in unwanted:
        if marker in prompt or marker in system:
            found_unwanted.append(marker)

    if found_unwanted:
        print(f"  - Unwanted markers: {', '.join(found_unwanted)}")
    else:
        print(f"  - Unwanted markers: NONE (Clean)")

    # Show first 200 chars of prompt
    print(f"\nFirst 200 chars of prompt:")
    print(f"  {prompt[:200]}...")

    # Show full system message
    print(f"\nFull system message:")
    print(f"  {system}")

print("\n" + "=" * 80)
print("\nSummary: Checking if all translations are clean and have correct placeholders")
