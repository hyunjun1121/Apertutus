import json
from pathlib import Path

def check_translation_quality():
    """Check quality of all translations in strong_reject.json"""

    with open('strong_reject.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("="*80)
    print("TRANSLATION QUALITY CHECK")
    print("="*80)

    # Get English original
    if 'eng.Latn' not in data:
        print("ERROR: English original not found!")
        return

    original_prompt = data['eng.Latn']['strongreject_prompt']
    original_system = data['eng.Latn']['strongreject_system']

    # Issues tracker
    all_issues = []

    for lang_code, content in data.items():
        if lang_code == 'eng.Latn':
            continue

        issues = []

        prompt = content.get('strongreject_prompt', '')
        system = content.get('strongreject_system', '')

        # 1. Check placeholders
        if '{forbidden_prompt}' not in prompt:
            issues.append("Missing {forbidden_prompt} in prompt")
        if '{response}' not in prompt:
            issues.append("Missing {response} in prompt")

        # 2. Check markers
        if '#scores' not in prompt.lower():
            issues.append("Missing #scores marker")
        if 'overall_reasoning' not in prompt.lower():
            issues.append("Missing overall_reasoning marker")

        # 3. Check for unwanted phrases
        unwanted = ['translate', 'translation', '번역', '翻译', 'remember', '기억',
                   'traduction', 'traduzione', 'traducción', 'tradução', 'übersetzung']

        for phrase in unwanted:
            if phrase.lower() in prompt.lower():
                issues.append(f"Contains unwanted phrase: '{phrase}'")
                break

        # 4. Length check (should be similar to original, allow 2x variation)
        original_len = len(original_prompt)
        translated_len = len(prompt)

        if translated_len > original_len * 2:
            issues.append(f"Too long: {translated_len} chars (original: {original_len})")
        elif translated_len < original_len * 0.3:
            issues.append(f"Too short: {translated_len} chars (original: {original_len})")

        # 5. Check system prompt
        if '{forbidden_prompt}' in original_system and '{forbidden_prompt}' not in system:
            issues.append("Missing {forbidden_prompt} in system")
        if '{response}' in original_system and '{response}' not in system:
            issues.append("Missing {response} in system")

        # Store results
        if issues:
            all_issues.append({
                'lang': lang_code,
                'issues': issues
            })

    # Print results
    print(f"\nChecked {len(data) - 1} languages\n")

    if all_issues:
        print("ISSUES FOUND:\n")
        for item in all_issues:
            print(f"{item['lang']}:")
            for issue in item['issues']:
                print(f"  - {issue}")
            print()
    else:
        print("✓ All translations look good!\n")

    # Summary statistics
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total languages: {len(data)}")
    print(f"Languages with issues: {len(all_issues)}")
    print(f"Clean translations: {len(data) - 1 - len(all_issues)}")

    # Save detailed report
    with open('translation_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write("TRANSLATION QUALITY REPORT\n")
        f.write("="*80 + "\n\n")

        for lang_code, content in data.items():
            if lang_code == 'eng.Latn':
                continue

            f.write(f"\n{'='*80}\n")
            f.write(f"Language: {lang_code}\n")
            f.write(f"{'='*80}\n\n")

            f.write("SYSTEM PROMPT:\n")
            f.write("-"*80 + "\n")
            f.write(content['strongreject_system'] + "\n\n")

            f.write("EVALUATION PROMPT (first 500 chars):\n")
            f.write("-"*80 + "\n")
            f.write(content['strongreject_prompt'][:500] + "...\n\n")

    print(f"\nDetailed report saved to: translation_quality_report.txt")

if __name__ == "__main__":
    check_translation_quality()
