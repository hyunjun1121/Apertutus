import json
import asyncio
from typing import Dict, Any, List
from apertus_api import ApertusAPI
from strongreject_evaluator import StrongRejectEvaluator
import os
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

class SafetyTester:
    def __init__(self, config_path: str = "config.json"):
        self.api = ApertusAPI(config_path)
        self.evaluator = StrongRejectEvaluator(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    async def execute_multi_turn_jailbreak(self, entry: Dict[str, Any]) -> List[str]:
        """Execute a multi-turn jailbreak attempt and collect responses"""
        responses = []
        conversation = []

        for turn in entry['turns']:
            # Add user message to conversation
            conversation.append({"role": "user", "content": turn['content']})

            # Get model response
            response = await self.api.acall_model(conversation, temperature=0.7)

            if response:
                responses.append(response)
                # Add assistant response to conversation for context
                conversation.append({"role": "assistant", "content": response})
            else:
                responses.append("")

        return responses

    async def test_single_entry(self, entry: Dict[str, Any], entry_index: int) -> Dict[str, Any]:
        """Test a single entry and evaluate it"""
        try:
            # Execute jailbreak
            print(f"  Testing entry {entry_index + 1}...")
            responses = await self.execute_multi_turn_jailbreak(entry)

            # Evaluate with StrongReject
            evaluation = await self.evaluator.evaluate_jailbreak_attempt(entry, responses)

            # Add results to entry
            result = entry.copy()
            result['jailbreak_responses'] = responses
            result['strongreject_evaluation'] = evaluation
            result['test_timestamp'] = datetime.now().isoformat()

            return result
        except Exception as e:
            print(f"  Error testing entry {entry_index + 1}: {e}")
            result = entry.copy()
            result['error'] = str(e)
            result['strongreject_evaluation'] = {
                'refused': 0,
                'convincing': 1,
                'specific': 1,
                'score': 1.0,
                'error': str(e)
            }
            return result

    async def test_dataset_batch(self, dataset: List[Dict[str, Any]],
                                language_name: str,
                                batch_size: int = 5) -> List[Dict[str, Any]]:
        """Test a dataset with batching for parallel processing"""
        results = []
        total = len(dataset)

        for i in range(0, total, batch_size):
            batch = dataset[i:i+batch_size]
            batch_end = min(i+batch_size, total)
            print(f"Testing {language_name} batch {i+1}-{batch_end}/{total}")

            # Test entries in parallel within batch
            tasks = []
            for j, entry in enumerate(batch):
                tasks.append(self.test_single_entry(entry, i+j))

            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Small delay between batches
            await asyncio.sleep(0.5)

        return results

    async def test_multilingual_datasets(self, dataset_dir: str = "multilingual_datasets",
                                        output_dir: str = "safety_test_results",
                                        languages_to_test: List[str] = None) -> Dict[str, str]:
        """Test all multilingual datasets"""
        os.makedirs(output_dir, exist_ok=True)

        # Get all dataset files
        dataset_files = [f for f in os.listdir(dataset_dir) if f.endswith('.json')]

        if languages_to_test:
            # Filter to specific languages
            dataset_files = [f for f in dataset_files
                            if any(lang in f for lang in languages_to_test)]

        output_files = {}

        for dataset_file in dataset_files:
            input_path = os.path.join(dataset_dir, dataset_file)
            language_code = dataset_file.replace('mhj_dataset_', '').replace('.json', '')

            print(f"\n{'='*60}")
            print(f"Testing dataset: {dataset_file}")
            print(f"Language: {language_code}")
            print(f"{'='*60}")

            # Load dataset
            with open(input_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)

            # Test dataset
            start_time = time.time()
            tested_data = await self.test_dataset_batch(dataset, language_code, batch_size=5)

            # Calculate statistics
            scores = [entry['strongreject_evaluation']['score']
                     for entry in tested_data
                     if 'strongreject_evaluation' in entry]
            refused_count = sum(1 for entry in tested_data
                              if entry.get('strongreject_evaluation', {}).get('refused', 0) == 1)

            stats = {
                'language': language_code,
                'total_tested': len(tested_data),
                'average_score': sum(scores) / len(scores) if scores else 0,
                'refused_count': refused_count,
                'refused_percentage': (refused_count / len(tested_data)) * 100 if tested_data else 0
            }

            # Save results
            output_file = os.path.join(output_dir, f"safety_results_{language_code}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'statistics': stats,
                    'tested_entries': tested_data
                }, f, indent=2, ensure_ascii=False)

            elapsed = time.time() - start_time
            print(f"\nCompleted {language_code} in {elapsed:.2f} seconds")
            print(f"Statistics:")
            print(f"  - Average Score: {stats['average_score']:.2f}")
            print(f"  - Refused: {stats['refused_count']}/{stats['total_tested']} ({stats['refused_percentage']:.1f}%)")
            print(f"  - Saved to: {output_file}")

            output_files[language_code] = output_file

        return output_files

class ParallelSafetyTester:
    """Enhanced safety tester with parallel API key utilization"""
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.api_keys = self.config['api_keys']
        self.testers = [SafetyTester(config_path) for _ in self.api_keys]

    async def run_parallel_tests(self, dataset_dir: str = "multilingual_datasets",
                               output_dir: str = "safety_test_results",
                               languages_to_test: List[str] = None):
        """Run tests in parallel using all API keys"""
        # Get all dataset files
        dataset_files = [f for f in os.listdir(dataset_dir) if f.endswith('.json')]

        if languages_to_test:
            dataset_files = [f for f in dataset_files
                            if any(lang in f for lang in languages_to_test)]

        # Distribute datasets among testers
        tasks = []
        for i, dataset_file in enumerate(dataset_files):
            tester = self.testers[i % len(self.testers)]
            task = tester.test_multilingual_datasets(
                dataset_dir, output_dir,
                [dataset_file.replace('mhj_dataset_', '').replace('.json', '')]
            )
            tasks.append(task)

        # Run all tests in parallel
        results = await asyncio.gather(*tasks)
        return results

def run_safety_test(parallel: bool = True, languages_to_test: List[str] = None):
    """Main function to run safety testing"""
    if parallel:
        print("Running parallel safety testing with multiple API keys...")
        tester = ParallelSafetyTester()
        asyncio.run(tester.run_parallel_tests(languages_to_test=languages_to_test))
    else:
        print("Running sequential safety testing...")
        tester = SafetyTester()
        asyncio.run(tester.test_multilingual_datasets(languages_to_test=languages_to_test))

if __name__ == "__main__":
    # Test with specific languages or all if None
    run_safety_test(parallel=True, languages_to_test=None)