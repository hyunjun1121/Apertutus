import json
import time
from typing import List, Dict, Any
from huggingface_hub import InferenceClient
from tqdm import tqdm
import os

class Apertus8BHFAPI:
    def __init__(self, hf_token: str):
        """Initialize Apertus 8B model using Hugging Face Inference API"""
        self.hf_token = hf_token
        self.model_name = "swiss-ai/Apertus-8B-2509"
        self.client = InferenceClient(
            model=self.model_name,
            token=self.hf_token
        )

    def generate_response(self, messages: List[Dict[str, str]],
                         temperature: float = 0.8,
                         max_tokens: int = 500,
                         top_p: float = 0.9) -> str:
        """Generate response using Apertus 8B model via HF Inference API"""
        try:
            # Format messages for the model
            formatted_prompt = self._format_messages(messages)

            # Generate response using HF Inference API
            response = self.client.text_generation(
                formatted_prompt,
                temperature=temperature,
                max_new_tokens=max_tokens,
                top_p=top_p,
                do_sample=True,
                return_full_text=False
            )

            return response

        except Exception as e:
            print(f"Error calling HF API: {e}")
            return None

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a prompt string for the model"""
        # Using simple format for now - can be adjusted based on model requirements
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"

        # Add final assistant prompt
        prompt += "Assistant:"
        return prompt

    def translate_text(self, text: str, target_language: str, language_name: str) -> str:
        """Translate text to target language using Apertus 8B"""
        try:
            # Load translation prompt template if exists
            try:
                with open('translation_prompt.txt', 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
            except FileNotFoundError:
                prompt_template = """Translate the following text to {target_language}.
Only provide the translation without any explanation.

Text: {sentence}"""

            translation_prompt = prompt_template.format(
                original_language="English",
                target_language=language_name,
                sentence=text
            )

            messages = [
                {"role": "user", "content": translation_prompt}
            ]

            response = self.generate_response(messages, temperature=0.3)

            # Parse translation from response
            if response and "Translation:" in response:
                translation = response.split("Translation:")[1].strip()
                return translation
            return response

        except Exception as e:
            print(f"Error in translation: {e}")
            return None

    def process_dataset(self, dataset_path: str, output_path: str = None,
                       start_idx: int = 0, end_idx: int = None):
        """Process a dataset file using Apertus 8B model"""

        # Load dataset
        print(f"Loading dataset from {dataset_path}")
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        # Handle indices
        if end_idx is None:
            end_idx = len(dataset)
        else:
            end_idx = min(end_idx, len(dataset))

        # Setup output path
        if output_path is None:
            base_name = os.path.basename(dataset_path).replace('.json', '')
            output_dir = "llm_responses_8b"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{base_name}_apertus8b_responses.json")

        # Check if partial results exist
        results = []
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            print(f"Resuming from {len(results)} existing results")
            start_idx = max(start_idx, len(results))

        print(f"Processing samples {start_idx} to {end_idx}")

        # Process each sample
        for i in tqdm(range(start_idx, end_idx), desc="Processing"):
            try:
                item = dataset[i]

                # Create messages
                messages = [
                    {"role": "system", "content": "You are a helpful assistant. Please respond in the same language as the user's input."},
                    {"role": "user", "content": item['instruction']}
                ]

                # Generate response
                response = self.generate_response(
                    messages=messages,
                    temperature=0.8,
                    max_tokens=500,
                    top_p=0.9
                )

                # Store result
                result = {
                    "id": item.get("id", i),
                    "instruction": item['instruction'],
                    "original_output": item.get('output', ''),
                    "llm_response": response,
                    "model": self.model_name
                }
                results.append(result)

                # Save intermediate results every 5 samples
                if (i - start_idx + 1) % 5 == 0:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    print(f"\nSaved {len(results)} samples to {output_path}")

                # Rate limiting - be respectful to HF API
                time.sleep(1)  # Adjust based on your HF API rate limits

            except Exception as e:
                print(f"\nError processing sample {i}: {e}")
                result = {
                    "id": item.get("id", i),
                    "instruction": item['instruction'],
                    "original_output": item.get('output', ''),
                    "llm_response": None,
                    "error": str(e),
                    "model": self.model_name
                }
                results.append(result)

        # Save final results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\nProcessing complete! Results saved to {output_path}")
        print(f"Processed {len(results)} samples")

        # Print summary
        successful = sum(1 for r in results if r.get('llm_response') is not None)
        failed = len(results) - successful
        print(f"Successful: {successful}, Failed: {failed}")

        return results