import json

# Load translations
with open("strong_reject.json", "r", encoding="utf-8") as f:
    data = json.load(f)

LANGUAGES = [
    "arb.Arab", "ces.Latn", "cmn.Hani", "deu.Latn", "fra.Latn", "ind.Latn",
    "ita.Latn", "jpn.Jpan", "kor.Hang", "nld.Latn", "pol.Latn", "por.Latn",
    "ron.Latn", "rus.Cyrl", "spa.Latn", "tur.Latn"
]

print("Final Translation Quality Check")
print("=" * 80)

issues_found = {}

for lang_code in LANGUAGES:
    prompt = data[lang_code]["strongreject_prompt"]
    system = data[lang_code]["strongreject_system"]

    lang_issues = []

    # Check placeholders in prompt
    if "{forbidden_prompt}" not in prompt:
        lang_issues.append("Missing {forbidden_prompt} in prompt")
    if "{response}" not in prompt:
        lang_issues.append("Missing {response} in prompt")

    # Check for empty translations
    if not prompt or not system:
        lang_issues.append("Empty translation")

    # Check for unwanted meta-commentary markers
    unwanted = ["Translation:", "Explanation:", "Note:", "Remember:", "Output:",
                "Here is", "Below is the translation", "I have translated"]
    for marker in unwanted:
        if marker in prompt[:500]:  # Check first 500 chars
            lang_issues.append(f"Contains meta-marker: {marker}")
            break

    # Check length (very short = likely failed)
    if len(prompt) < 500:
        lang_issues.append(f"Suspiciously short prompt ({len(prompt)} chars)")

    if lang_issues:
        issues_found[lang_code] = lang_issues

# Print results
if issues_found:
    print("\nISSUES FOUND:\n")
    for lang_code, issues in issues_found.items():
        print(f"{lang_code}:")
        for issue in issues:
            print(f"  - {issue}")
        print()
else:
    print("\nALL TRANSLATIONS PASSED!")
    print("\nSummary:")
    for lang_code in LANGUAGES:
        prompt_len = len(data[lang_code]["strongreject_prompt"])
        system_len = len(data[lang_code]["strongreject_system"])
        print(f"{lang_code}: Prompt {prompt_len} chars, System {system_len} chars - OK")

print("\n" + "=" * 80)
