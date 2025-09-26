"""
Batch translator for tmux - Split workload across multiple terminal sessions
"""

import json
import os
import argparse
from typing import List, Dict, Any
from apertus_api import ApertusAPI
import time
from datetime import datetime

class TmuxBatchTranslator:
    def __init__(self, config_path: str = "config.json", api_key_index: int = 0):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.languages = self.config['languages']

        # Use specific API key for this instance
        if api_key_index < len(self.config['api_keys']):
            api_key = self.config['api_keys'][api_key_index]
        else:
            api_key = self.config['api_keys'][0]

        self.api = ApertusAPI(config_path)
        self.api.api_keys = [api_key]
        self.api.current_key_index = 0
        self.api_key_index = api_key_index

    def translate_turn(self, turn: Dict[str, Any], target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate a single turn"""
        try:
            translated_content = self.api.translate_text(
                text=turn['content'],
                target_language=target_language['code'],
                language_name=target_language['name']
            )

            return {
                'turn_number': turn['turn_number'],
                'content': translated_content if translated_content else turn['content'],
                'original_content': turn['content']  # Always save original
            }
        except Exception as e:
            print(f"  Error translating turn {turn['turn_number']}: {e}")
            return {
                'turn_number': turn['turn_number'],
                'content': turn['content'],
                'original_content': turn['content'],
                'translation_error': str(e)
            }

    def translate_entry(self, entry: Dict[str, Any], target_language: Dict[str, str],
                       entry_index: int) -> Dict[str, Any]:
        """Translate all turns in an entry"""
        translated_turns = []

        for turn in entry['turns']:
            translated_turn = self.translate_turn(turn, target_language)
            translated_turns.append(translated_turn)
            time.sleep(0.05)  # Small delay

        return {
            'entry_index': entry_index,  # Track original index
            'source': entry['source'],
            'base_prompt': entry['base_prompt'],  # Keep English
            'original_base_prompt': entry['base_prompt'],  # Also save as original
            'turn_type': entry['turn_type'],
            'num_turns': entry['num_turns'],
            'turns': translated_turns,
            'language_code': target_language['code'],
            'language_name': target_language['name']
        }

    def translate_language_range(self, dataset: List[Dict[str, Any]],
                                language: Dict[str, str],
                                start_idx: int,
                                end_idx: int,
                                output_dir: str = "multilingual_datasets"):
        """Translate a specific range of entries for one language"""
        os.makedirs(output_dir, exist_ok=True)

        # Output file for this specific chunk
        output_file = os.path.join(output_dir,
            f"mhj_dataset_{language['code']}_part{start_idx}-{end_idx}.json")

        print(f"Translating entries {start_idx}-{end_idx} to {language['name']}")
        print(f"Using API key index: {self.api_key_index}")
        print(f"Output: {output_file}")

        translated_data = []
        for i in range(start_idx, min(end_idx, len(dataset))):
            if (i - start_idx + 1) % 10 == 0:
                print(f"  Progress: {i - start_idx + 1}/{end_idx - start_idx} entries")

            translated_entry = self.translate_entry(dataset[i], language, i)
            translated_data.append(translated_entry)

        # Save partial results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(translated_data)} entries to {output_file}")
        return output_file

def merge_translation_parts(language_code: str,
                           input_dir: str = "multilingual_datasets",
                           output_dir: str = "multilingual_datasets"):
    """Merge all parts of a translated language into single file"""
    import glob

    # Find all parts for this language
    pattern = os.path.join(input_dir, f"mhj_dataset_{language_code}_part*.json")
    part_files = sorted(glob.glob(pattern))

    if not part_files:
        print(f"No parts found for {language_code}")
        return None

    print(f"Found {len(part_files)} parts for {language_code}")

    # Collect all entries
    all_entries = []
    for part_file in part_files:
        with open(part_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
            all_entries.extend(entries)

    # Sort by original index
    all_entries.sort(key=lambda x: x.get('entry_index', 0))

    # Save merged file
    output_file = os.path.join(output_dir, f"mhj_dataset_{language_code}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    print(f"✓ Merged {len(all_entries)} entries into {output_file}")

    # Optionally delete part files
    # for part_file in part_files:
    #     os.remove(part_file)

    return output_file

def generate_tmux_commands(total_entries: int = 537, languages: List[str] = None,
                          entries_per_session: int = 100):
    """Generate tmux commands for parallel execution"""

    if languages is None:
        # Default to first 5 languages for testing
        languages = ["kor.Hang", "fra.Latn", "deu.Latn", "spa.Latn", "jpn.Jpan"]

    commands = []
    session_idx = 0

    for lang_idx, language in enumerate(languages):
        # Split entries into chunks
        for start in range(0, total_entries, entries_per_session):
            end = min(start + entries_per_session, total_entries)
            api_key_idx = session_idx % 5  # Rotate through 5 API keys

            cmd = f"python tmux_batch_translator.py --language {language} --start {start} --end {end} --api-key {api_key_idx}"

            tmux_cmd = f"tmux new-session -d -s 'trans_{language}_{start}' '{cmd}'"
            commands.append({
                'session': f'trans_{language}_{start}',
                'command': cmd,
                'tmux': tmux_cmd
            })

            session_idx += 1

    return commands

def main():
    parser = argparse.ArgumentParser(description='Batch translator for tmux execution')
    parser.add_argument('--language', type=str, required=False,
                       help='Language code to translate (e.g., kor.Hang)')
    parser.add_argument('--start', type=int, default=0,
                       help='Start index for entries')
    parser.add_argument('--end', type=int, default=100,
                       help='End index for entries')
    parser.add_argument('--api-key', type=int, default=0,
                       help='API key index to use (0-4)')
    parser.add_argument('--merge', type=str,
                       help='Merge parts for specified language code')
    parser.add_argument('--generate-commands', action='store_true',
                       help='Generate tmux commands for parallel execution')

    args = parser.parse_args()

    # Generate tmux commands
    if args.generate_commands:
        print("=" * 60)
        print("TMUX COMMANDS FOR PARALLEL EXECUTION")
        print("=" * 60)

        commands = generate_tmux_commands()

        print(f"Generated {len(commands)} tmux sessions\n")

        print("Run these commands in your terminal:")
        print("-" * 40)
        for cmd_info in commands:
            print(cmd_info['tmux'])

        print("\n" + "-" * 40)
        print("To monitor progress:")
        print("tmux ls  # List all sessions")
        print("tmux attach -t trans_kor.Hang_0  # Attach to specific session")

        print("\n" + "-" * 40)
        print("After completion, merge results:")
        for lang in ["kor.Hang", "fra.Latn", "deu.Latn", "spa.Latn", "jpn.Jpan"]:
            print(f"python tmux_batch_translator.py --merge {lang}")

        return

    # Merge operation
    if args.merge:
        merge_translation_parts(args.merge)
        return

    # Translation operation
    if not args.language:
        print("Error: --language is required for translation")
        return

    # Load dataset
    with open("mhj_dataset.json", 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Get language details
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)

    language = None
    for lang in config['languages']:
        if lang['code'] == args.language:
            language = lang
            break

    if not language:
        print(f"Error: Language {args.language} not found")
        return

    # Create translator and run
    translator = TmuxBatchTranslator(api_key_index=args.api_key)

    start_time = time.time()
    translator.translate_language_range(
        dataset, language, args.start, args.end
    )

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f} seconds")

if __name__ == "__main__":
    main()