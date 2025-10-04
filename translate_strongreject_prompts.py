import json
import asyncio
from pathlib import Path
from apertus_api import ApertusAPI

# Language mapping
LANGUAGES = {
    'arb.Arab': {'name': 'Arabic', 'script': 'Arab'},
    'ces.Latn': {'name': 'Czech', 'script': 'Latn'},
    'cmn.Hani': {'name': 'Chinese (Mandarin)', 'script': 'Hani'},
    'deu.Latn': {'name': 'German', 'script': 'Latn'},
    'fra.Latn': {'name': 'French', 'script': 'Latn'},
    'ind.Latn': {'name': 'Indonesian', 'script': 'Latn'},
    'ita.Latn': {'name': 'Italian', 'script': 'Latn'},
    'jpn.Jpan': {'name': 'Japanese', 'script': 'Jpan'},
    'kor.Hang': {'name': 'Korean', 'script': 'Hang'},
    'nld.Latn': {'name': 'Dutch', 'script': 'Latn'},
    'pol.Latn': {'name': 'Polish', 'script': 'Latn'},
    'por.Latn': {'name': 'Portuguese', 'script': 'Latn'},
    'ron.Latn': {'name': 'Romanian', 'script': 'Latn'},
    'rus.Cyrl': {'name': 'Russian', 'script': 'Cyrl'},
    'spa.Latn': {'name': 'Spanish', 'script': 'Latn'},
    'tur.Latn': {'name': 'Turkish', 'script': 'Latn'}
}

class StrongRejectTranslator:
    def __init__(self):
        # Hardcoded API key
        api_keys = ["FVNVGZmSngy18jUzod50WdcIIUBq"]
        self.api = ApertusAPI(api_keys)

    def load_original_prompts(self):
        """Load original English prompts"""
        with open('strong_reject.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    async def translate_text(self, text, target_language_name):
        """Translate text to target language using Apertus API"""

        # Use the proven translation template from mhj dataset
        translation_prompt = f"""You are an expert translator specializing in English and {target_language_name}.
Your task is to translate the given English text into {target_language_name} while maintaining its formal, technical tone.

### Guidelines:
- Translate the text accurately while preserving its professional and technical nature
- Preserve ALL special formatting:
  * Placeholder variables: {{forbidden_prompt}}, {{response}}
  * Special markers: #scores, #overall_reasoning, etc.
  * Line breaks and paragraph structure
  * Numbered lists (1., 2., 3.)
  * Bullet points (-)
- Do NOT translate placeholder variables in curly braces {{}}
- Do NOT translate special markers starting with #
- Maintain the formal, instructional tone

### Output Format:
Translation:
<your translated text ONLY, without any explanation>

Now, translate the following text:
English: "{text}"
"""

        messages = [
            {"role": "user", "content": translation_prompt}
        ]

        response = await self.api.acall_model(
            messages=messages,
            temperature=0.1,
            max_tokens=4000
        )

        if response:
            # Post-processing: extract only the translation part
            cleaned = response.strip()

            # Extract text after "Translation:" marker
            if "Translation:" in cleaned:
                parts = cleaned.split("Translation:", 1)
                if len(parts) > 1:
                    cleaned = parts[1].strip()

            # Remove common unwanted patterns at the start
            unwanted_patterns = [
                "Here is the translation:",
                "Translated text:",
                "以下是翻译:",
                "翻译:",
                "번역:",
                "다음은 번역입니다:",
                "Übersetzung:",
                "Traduction:",
                "Traduzione:",
                "Traducción:",
                "Tradução:",
                "Перевод:"
            ]

            for pattern in unwanted_patterns:
                if cleaned.startswith(pattern):
                    cleaned = cleaned[len(pattern):].strip()

            return cleaned

        return None

    async def translate_all_languages(self):
        """Translate prompts to all 16 languages"""
        # Load original prompts
        original_data = self.load_original_prompts()

        # Start with original English version
        result = {
            'eng.Latn': {
                'strongreject_prompt': original_data['strongreject_prompt'],
                'strongreject_system': original_data['strongreject_system']
            }
        }

        print("=" * 80)
        print("TRANSLATING STRONGREJECT PROMPTS TO 16 LANGUAGES")
        print("=" * 80)

        for lang_code, lang_info in LANGUAGES.items():
            lang_name = lang_info['name']
            print(f"\nTranslating to {lang_name} ({lang_code})...")

            try:
                # Translate strongreject_prompt
                print(f"  - Translating strongreject_prompt...")
                translated_prompt = await self.translate_text(
                    original_data['strongreject_prompt'],
                    lang_name
                )

                # Translate strongreject_system
                print(f"  - Translating strongreject_system...")
                translated_system = await self.translate_text(
                    original_data['strongreject_system'],
                    lang_name
                )

                if translated_prompt and translated_system:
                    result[lang_code] = {
                        'strongreject_prompt': translated_prompt,
                        'strongreject_system': translated_system
                    }
                    print(f"  [SUCCESS] {lang_name} translation completed")
                else:
                    print(f"  [FAILED] {lang_name} translation failed")

            except Exception as e:
                print(f"  [ERROR] Failed to translate {lang_name}: {e}")

        return result

    def validate_translation(self, original_text, translated_text, lang_name):
        """Validate translation quality"""
        issues = []

        # Check placeholders are preserved
        if '{forbidden_prompt}' in original_text and '{forbidden_prompt}' not in translated_text:
            issues.append("Missing {forbidden_prompt}")
        if '{response}' in original_text and '{response}' not in translated_text:
            issues.append("Missing {response}")

        # Check if translation is suspiciously long (>3x original)
        if len(translated_text) > len(original_text) * 3:
            issues.append(f"Translation too long ({len(translated_text)} vs {len(original_text)} chars)")

        # Check for unwanted phrases that might indicate meta-commentary
        unwanted_phrases = ['translate', 'translation', '翻译', '번역', 'Übersetzung',
                           'Traduction', 'Traduzione', 'Traducción', 'Tradução', 'Перевод']
        for phrase in unwanted_phrases:
            if phrase.lower() in translated_text.lower():
                issues.append(f"Contains unwanted phrase: {phrase}")

        return issues

    def save_translations(self, translations):
        """Save translations to strong_reject.json with backup"""
        output_file = 'strong_reject.json'
        backup_file = 'strong_reject_backup.json'

        # Create backup of existing file
        if Path(output_file).exists():
            import shutil
            shutil.copy(output_file, backup_file)
            print(f"Backup created: {backup_file}")

        # Validate all translations before saving
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)

        all_valid = True
        for lang_code, content in translations.items():
            if lang_code == 'eng.Latn':
                continue

            # Get original for comparison
            original = translations['eng.Latn']

            # Validate system prompt
            issues_system = self.validate_translation(
                original['strongreject_system'],
                content['strongreject_system'],
                lang_code
            )

            # Validate main prompt
            issues_prompt = self.validate_translation(
                original['strongreject_prompt'],
                content['strongreject_prompt'],
                lang_code
            )

            all_issues = issues_system + issues_prompt

            if all_issues:
                all_valid = False
                print(f"\n{lang_code}:")
                for issue in all_issues:
                    print(f"  [WARNING] {issue}")
            else:
                print(f"{lang_code}: OK")

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 80)
        print(f"Translations saved to {output_file}")
        print(f"Total languages: {len(translations)}")
        if all_valid:
            print("Status: All validations passed!")
        else:
            print("Status: Some warnings detected (review above)")
        print("=" * 80)

async def main():
    translator = StrongRejectTranslator()

    # Translate to all languages
    translations = await translator.translate_all_languages()

    # Save to file
    translator.save_translations(translations)

    print("\n[DONE] All translations completed!")

if __name__ == "__main__":
    asyncio.run(main())