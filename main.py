"""
Multilingual Safety Testing System for Apertus Model

This script orchestrates the complete workflow:
1. Translate MHJ dataset to multiple languages
2. Run safety tests on all multilingual datasets
3. Evaluate responses using StrongReject
4. Generate comprehensive reports
"""

import asyncio
import json
import os
import sys
from datetime import datetime
import argparse
from typing import List

from multilingual_translator import MultilingualTranslator
from safety_tester import run_safety_test

def load_config(config_path: str = "config.json") -> dict:
    """Load configuration file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_summary_report(results_dir: str = "safety_test_results") -> None:
    """Generate a summary report from all test results"""
    summary = {
        'timestamp': datetime.now().isoformat(),
        'languages': {},
        'overall_statistics': {
            'total_languages': 0,
            'total_tests': 0,
            'overall_average_score': 0,
            'overall_refused_percentage': 0
        }
    }

    result_files = [f for f in os.listdir(results_dir) if f.startswith('safety_results_')]

    all_scores = []
    all_refused_counts = []
    all_totals = []

    for result_file in result_files:
        with open(os.path.join(results_dir, result_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            stats = data['statistics']

            language_code = stats['language']
            summary['languages'][language_code] = {
                'average_score': stats['average_score'],
                'refused_percentage': stats['refused_percentage'],
                'total_tested': stats['total_tested']
            }

            all_scores.append(stats['average_score'] * stats['total_tested'])
            all_refused_counts.append(stats['refused_count'])
            all_totals.append(stats['total_tested'])

    # Calculate overall statistics
    total_tests = sum(all_totals)
    summary['overall_statistics']['total_languages'] = len(result_files)
    summary['overall_statistics']['total_tests'] = total_tests
    summary['overall_statistics']['overall_average_score'] = sum(all_scores) / total_tests if total_tests > 0 else 0
    summary['overall_statistics']['overall_refused_percentage'] = (sum(all_refused_counts) / total_tests * 100) if total_tests > 0 else 0

    # Save summary report
    report_path = os.path.join(results_dir, 'summary_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print("SAFETY TESTING SUMMARY REPORT")
    print("="*60)
    print(f"Total Languages Tested: {summary['overall_statistics']['total_languages']}")
    print(f"Total Tests Run: {summary['overall_statistics']['total_tests']}")
    print(f"Overall Average Score: {summary['overall_statistics']['overall_average_score']:.2f}")
    print(f"Overall Refused Rate: {summary['overall_statistics']['overall_refused_percentage']:.1f}%")
    print("\nPer-Language Results:")
    for lang, stats in summary['languages'].items():
        print(f"  {lang}: Score={stats['average_score']:.2f}, Refused={stats['refused_percentage']:.1f}%")
    print(f"\nFull report saved to: {report_path}")

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Multilingual Safety Testing for Apertus Model')
    parser.add_argument('--translate', action='store_true',
                       help='Run translation step to create multilingual datasets')
    parser.add_argument('--test', action='store_true',
                       help='Run safety testing on multilingual datasets')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='Use parallel processing with multiple API keys')
    parser.add_argument('--languages', nargs='+',
                       help='Specific language codes to test (e.g., kor.Hang fra.Latn)')
    parser.add_argument('--config', default='config.json',
                       help='Path to configuration file')

    args = parser.parse_args()

    # If no specific action, run both
    if not args.translate and not args.test:
        args.translate = True
        args.test = True

    print("="*60)
    print("MULTILINGUAL SAFETY TESTING SYSTEM")
    print("="*60)
    print(f"Configuration: {args.config}")
    print(f"Parallel Processing: {args.parallel}")
    if args.languages:
        print(f"Target Languages: {', '.join(args.languages)}")
    print()

    # Step 1: Translation
    if args.translate:
        print("\n" + "="*60)
        print("STEP 1: TRANSLATING DATASET TO MULTIPLE LANGUAGES")
        print("="*60)

        translator = MultilingualTranslator(args.config)

        if args.languages:
            # Filter languages based on command line argument
            config = load_config(args.config)
            filtered_languages = [lang for lang in config['languages']
                                 if lang['code'] in args.languages]
            translator.languages = filtered_languages

        output_files = await translator.translate_to_all_languages()
        print(f"\n✓ Translation complete. Generated {len(output_files)} datasets.")

    # Step 2: Safety Testing
    if args.test:
        print("\n" + "="*60)
        print("STEP 2: RUNNING SAFETY TESTS")
        print("="*60)

        # Check if multilingual datasets exist
        if not os.path.exists("multilingual_datasets"):
            print("ERROR: No multilingual datasets found. Please run translation first.")
            return

        # Run safety testing
        await asyncio.create_task(
            asyncio.to_thread(run_safety_test, args.parallel, args.languages)
        )

        # Generate summary report
        print("\n" + "="*60)
        print("STEP 3: GENERATING SUMMARY REPORT")
        print("="*60)
        generate_summary_report()

    print("\n" + "="*60)
    print("PROCESS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())