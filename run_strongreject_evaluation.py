import json
import asyncio
from pathlib import Path
from typing import Dict, List
import argparse
from datetime import datetime, timedelta
from strongreject_evaluator import StrongRejectEvaluator
import pandas as pd
import sys
import time

class StrongRejectRunner:
    def __init__(self):
        self.evaluator = StrongRejectEvaluator()

    async def evaluate_language_file(self, filepath: Path, lang_idx: int = 0, total_langs: int = 1) -> Dict:
        """Evaluate all responses in a single language file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        language = filepath.stem.split('_')[2]  # Extract language code
        start_time = time.time()

        results = []
        total_score = 0
        total_refused = 0
        total_turns = 0
        total_entries = len(data)

        for entry_idx, entry in enumerate(data):
            # Real-time progress display
            if entry_idx % 10 == 0 or entry_idx == total_entries - 1:
                elapsed = time.time() - start_time
                progress = (entry_idx / total_entries) * 100

                # Calculate ETA
                if entry_idx > 0:
                    rate = entry_idx / elapsed
                    remaining = total_entries - entry_idx
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_str = str(timedelta(seconds=int(eta_seconds)))
                else:
                    eta_str = "calculating..."

                # Clear line and print progress
                sys.stdout.write('\r' + ' ' * 100 + '\r')
                sys.stdout.write(f"[{lang_idx+1}/{total_langs}] {language}: "
                               f"[{'█' * int(progress/5):<20}] "
                               f"{progress:.1f}% ({entry_idx}/{total_entries}) "
                               f"ETA: {eta_str}")
                sys.stdout.flush()

            entry_results = {
                'entry_index': entry.get('entry_index', entry_idx),
                'turn_evaluations': []
            }

            turns = entry.get('turns', [])

            # Collect all responses for this entry
            all_responses = []
            first_forbidden_prompt = ""
            has_valid_response = False

            for turn_idx, turn in enumerate(turns):
                if 'llm_response' in turn:
                    response = turn['llm_response']

                    # Skip error responses
                    if not response.startswith('ERROR:'):
                        all_responses.append(response)
                        has_valid_response = True

                    # Get first harmful prompt as the main forbidden prompt
                    if turn_idx == 0:
                        first_forbidden_prompt = turn.get('content', '')

            # Evaluate the combined response if we have valid responses
            if has_valid_response and first_forbidden_prompt:
                # Combine all responses into one
                combined_model_response = " ".join(all_responses)

                # Evaluate using StrongReject
                try:
                    evaluation = await self.evaluator.evaluate_response(
                        first_forbidden_prompt,
                        combined_model_response
                    )

                    evaluation['num_turns_combined'] = len(all_responses)
                    entry_results['combined_evaluation'] = evaluation

                    total_score += evaluation['score']
                    total_refused += evaluation['refused']
                    total_turns += 1

                except Exception as e:
                    print(f"    Error evaluating entry {entry_idx}: {e}")

            results.append(entry_results)

        # Final progress update
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        elapsed = time.time() - start_time
        print(f"[{lang_idx+1}/{total_langs}] {language}: "
              f"COMPLETE - {total_entries} entries, {total_turns} turns evaluated in {elapsed:.1f}s")

        # Calculate statistics
        stats = {
            'total_turns': total_turns,
            'total_refused': total_refused,
            'average_score': total_score / total_turns if total_turns > 0 else 0,
            'refusal_rate': (total_refused / total_turns * 100) if total_turns > 0 else 0,
            'compliance_rate': ((total_turns - total_refused) / total_turns * 100) if total_turns > 0 else 0
        }

        return {
            'language': language,
            'filepath': str(filepath),
            'statistics': stats,
            'detailed_results': results
        }

    async def evaluate_all_languages(self, response_dir: Path) -> Dict:
        """Evaluate all language response files"""
        response_files = sorted(response_dir.glob('mhj_dataset_*_with_responses.json'))
        total_files = len(response_files)

        print(f"=" * 60)
        print(f"STRONGREJECT EVALUATION STARTING")
        print(f"Found {total_files} response files to evaluate")
        print(f"Evaluator: Apertus-70B as judge")
        print(f"=" * 60)
        print()

        all_results = {}
        overall_start = time.time()

        for idx, filepath in enumerate(response_files):
            language = filepath.stem.split('_')[2]
            try:
                results = await self.evaluate_language_file(filepath, idx, total_files)
                all_results[language] = results

                stats = results['statistics']
                print(f"  → Refusal Rate: {stats['refusal_rate']:.1f}%, "
                      f"Avg Score: {stats['average_score']:.2f}\n")

            except Exception as e:
                print(f"Error evaluating {language}: {e}")
                all_results[language] = {'error': str(e)}

        overall_elapsed = time.time() - overall_start
        print(f"=" * 60)
        print(f"Total evaluation time: {str(timedelta(seconds=int(overall_elapsed)))}")

        return all_results

    def generate_report(self, results: Dict, output_file: str):
        """Generate evaluation report"""
        report = {
            'evaluation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'evaluation_model': 'Apertus-70B (as judge)',
            'total_languages': len(results),
            'language_results': {},
            'overall_statistics': {
                'total_turns': 0,
                'total_refused': 0,
                'total_score': 0,
            }
        }

        # Aggregate statistics
        for language, lang_results in results.items():
            if 'error' in lang_results:
                continue

            stats = lang_results['statistics']
            report['language_results'][language] = stats

            # Update overall stats
            report['overall_statistics']['total_turns'] += stats['total_turns']
            report['overall_statistics']['total_refused'] += stats['total_refused']
            report['overall_statistics']['total_score'] += stats['average_score'] * stats['total_turns']

        # Calculate overall percentages
        total = report['overall_statistics']['total_turns']
        if total > 0:
            report['overall_statistics']['overall_refusal_rate'] = \
                (report['overall_statistics']['total_refused'] / total) * 100
            report['overall_statistics']['overall_avg_score'] = \
                report['overall_statistics']['total_score'] / total

        # Save detailed report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Generate summary CSV
        csv_file = output_file.replace('.json', '.csv')
        df_data = []
        for language, stats in report['language_results'].items():
            df_data.append({
                'Language': language,
                'Total Turns': stats['total_turns'],
                'Refusal Rate %': f"{stats['refusal_rate']:.1f}",
                'Compliance Rate %': f"{stats['compliance_rate']:.1f}",
                'Average Score': f"{stats['average_score']:.2f}",
                'Total Refused': stats['total_refused']
            })

        df = pd.DataFrame(df_data)
        df.to_csv(csv_file, index=False)

        print("\n" + "=" * 60)
        print("STRONGREJECT EVALUATION SUMMARY")
        print("=" * 60)
        print(df.to_string(index=False))

        print("\n" + "=" * 60)
        print("OVERALL STATISTICS")
        print("=" * 60)
        print(f"Total Turns Evaluated: {total}")
        print(f"Overall Refusal Rate: {report['overall_statistics'].get('overall_refusal_rate', 0):.1f}%")
        print(f"Overall Average Score: {report['overall_statistics'].get('overall_avg_score', 0):.2f}")
        print("\nNote: Lower scores are better (0 = perfect refusal, 5 = full compliance)")

        print(f"\nReports saved:")
        print(f"  - Detailed: {output_file}")
        print(f"  - Summary: {csv_file}")

        return report

async def main():
    parser = argparse.ArgumentParser(description='Evaluate LLM responses using StrongReject')
    parser.add_argument('--dir', type=str, default='llm_responses',
                      help='Directory containing response files')
    parser.add_argument('--output', type=str, default='evaluation_results/strongreject_report.json',
                      help='Output report filename')
    parser.add_argument('--language', type=str,
                      help='Evaluate specific language only')

    args = parser.parse_args()

    # Create output directory
    Path('evaluation_results').mkdir(exist_ok=True)

    runner = StrongRejectRunner()

    if args.language:
        # Evaluate single language
        filepath = Path(args.dir) / f'mhj_dataset_{args.language}_with_responses.json'
        if filepath.exists():
            results = await runner.evaluate_language_file(filepath)
            print(json.dumps(results['statistics'], indent=2))
        else:
            print(f"File not found: {filepath}")
    else:
        # Evaluate all languages
        results = await runner.evaluate_all_languages(Path(args.dir))
        runner.generate_report(results, args.output)

if __name__ == "__main__":
    asyncio.run(main())