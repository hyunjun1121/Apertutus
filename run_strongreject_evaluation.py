import json
import asyncio
from pathlib import Path
from typing import Dict, List
import argparse
from datetime import datetime
from strongreject_evaluator import StrongRejectEvaluator
import pandas as pd

class StrongRejectRunner:
    def __init__(self):
        self.evaluator = StrongRejectEvaluator()

    async def evaluate_language_file(self, filepath: Path) -> Dict:
        """Evaluate all responses in a single language file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        language = filepath.stem.split('_')[2]  # Extract language code
        print(f"Evaluating {language}...")

        results = []
        total_score = 0
        total_refused = 0
        total_turns = 0

        for entry_idx, entry in enumerate(data):
            if entry_idx % 50 == 0:
                print(f"  Processing entry {entry_idx}/{len(data)}")

            entry_results = {
                'entry_index': entry.get('entry_index', entry_idx),
                'turn_evaluations': []
            }

            turns = entry.get('turns', [])

            for turn_idx, turn in enumerate(turns):
                if 'llm_response' in turn:
                    # Get the original harmful prompt (content)
                    forbidden_prompt = turn.get('content', '')
                    model_response = turn['llm_response']

                    # Skip error responses
                    if model_response.startswith('ERROR:'):
                        continue

                    # Evaluate using StrongReject
                    try:
                        evaluation = await self.evaluator.evaluate_response(
                            forbidden_prompt,
                            model_response
                        )

                        evaluation['turn_number'] = turn.get('turn_number', turn_idx + 1)
                        entry_results['turn_evaluations'].append(evaluation)

                        total_score += evaluation['score']
                        total_refused += evaluation['refused']
                        total_turns += 1

                    except Exception as e:
                        print(f"    Error evaluating turn {turn_idx}: {e}")

            results.append(entry_results)

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

        print(f"Found {len(response_files)} response files to evaluate")
        print("=" * 60)

        all_results = {}

        for filepath in response_files:
            language = filepath.stem.split('_')[2]
            try:
                results = await self.evaluate_language_file(filepath)
                all_results[language] = results

                stats = results['statistics']
                print(f"{language}: Refusal Rate: {stats['refusal_rate']:.1f}%, "
                      f"Avg Score: {stats['average_score']:.2f}")

            except Exception as e:
                print(f"Error evaluating {language}: {e}")
                all_results[language] = {'error': str(e)}

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