"""
Script to run translation of MHJ dataset to multiple languages
"""

import asyncio
from multilingual_translator import MultilingualTranslator
import sys

async def main():
    print("="*60)
    print("Starting Multilingual Translation")
    print("="*60)

    translator = MultilingualTranslator()

    # You can specify specific languages here or use all from config
    # For testing, you might want to start with just one language:
    # translator.languages = [{"code": "kor.Hang", "name": "Korean"}]

    print(f"Will translate to {len(translator.languages)} languages")
    print("Languages:", [lang['name'] for lang in translator.languages[:5]], "...")

    try:
        output_files = await translator.translate_to_all_languages(
            input_file="mhj_dataset.json",
            output_dir="multilingual_datasets"
        )

        print("\n" + "="*60)
        print("Translation Complete!")
        print(f"Created {len(output_files)} datasets")
        print("="*60)

    except Exception as e:
        print(f"Error during translation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # For testing with just Korean:
    # python run_translation.py

    asyncio.run(main())