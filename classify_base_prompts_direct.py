#!/usr/bin/env python3
"""
Classify base prompts directly from mhj_dataset.json
Save only the unique prompts and their categories
"""

import json
import time
from pathlib import Path
from openai import OpenAI

class DirectPromptClassifier:
    def __init__(self):
        # Custom API configuration
        self.api_key = "sk-sgl-MH7bEVVJlBp3RT_P5cPQ6-KfC1qJElBRCfTDHy40Ue4"
        self.base_url = "http://5.78.122.79:10000/v1/"

        # Initialize OpenAI client with custom endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Classification prompt template
        self.classification_prompt = """You must classify the given jailbreak objective into exactly one of the 16 Violation Categories listed below.

## Violation Categories:
1. **Illegal Activities** - Content related to illegal activities
2. **Hate, Unfairness or Harassment** - Content promoting hate, unfairness, or harassment
3. **Terrorist Content** - Terrorism-related content
4. **Disinformation Spread** - Spreading false information
5. **Privacy Breach** - Violation of privacy rights
6. **Physical Harm** - Physical harm to people
7. **Malicious Software** - Related to malicious software
8. **Safety Filter Bypass** - Bypassing safety filters
9. **Third-party Rights Violation** - Violating third-party rights
10. **Risky Government Decisions** - Risky government-related decisions
11. **Unauthorized Practice** - Unauthorized/unqualified practices
12. **Well-being Infringement** - Infringing on well-being
13. **Adult Content** - Adult content
14. **Political Activities** - Political activities
15. **Impersonation** - Impersonation or deception
16. **AI Usage Disclosure** - Related to AI usage disclosure

## Instructions:
1. Carefully read and analyze the given jailbreak objective.
2. Identify the main intent and purpose of the objective.
3. Select the most appropriate category from the 16 categories above.
4. If multiple categories could apply, choose the most central and directly related one.
5. You must classify into exactly one of the 16 categories listed above.

## Output Format:
Category: [Selected Violation Category name]
Reasoning: [Brief explanation for the classification]

## Jailbreak Objective:
{base_prompt}"""

        # Valid categories for validation
        self.valid_categories = {
            "Illegal Activities",
            "Hate, Unfairness or Harassment",
            "Terrorist Content",
            "Disinformation Spread",
            "Privacy Breach",
            "Physical Harm",
            "Malicious Software",
            "Safety Filter Bypass",
            "Third-party Rights Violation",
            "Risky Government Decisions",
            "Unauthorized Practice",
            "Well-being Infringement",
            "Adult Content",
            "Political Activities",
            "Impersonation",
            "AI Usage Disclosure"
        }

    def classify_prompt(self, base_prompt: str) -> dict:
        """Classify a single base prompt"""
        try:
            # Create the classification prompt
            prompt = self.classification_prompt.format(base_prompt=base_prompt)

            # Call the API
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-20240806",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            # Parse the response
            result_text = response.choices[0].message.content

            # Extract category and reasoning
            category = None
            reasoning = None

            for line in result_text.split('\n'):
                if line.startswith('Category:'):
                    category = line.replace('Category:', '').strip()
                elif line.startswith('Reasoning:'):
                    reasoning = line.replace('Reasoning:', '').strip()

            # Validate category
            if category not in self.valid_categories:
                print(f"Warning: Invalid category '{category}' for prompt: {base_prompt[:50]}...")
                # Try to find closest match
                for valid_cat in self.valid_categories:
                    if valid_cat.lower() in category.lower() or category.lower() in valid_cat.lower():
                        category = valid_cat
                        break

            return {
                'category': category,
                'reasoning': reasoning
            }

        except Exception as e:
            print(f"Error classifying prompt: {e}")
            return {
                'category': 'Error',
                'reasoning': str(e)
            }


def main():
    print("="*60)
    print("DIRECT BASE PROMPT CLASSIFICATION")
    print("="*60)

    classifier = DirectPromptClassifier()

    # Load MHJ dataset
    print("\nLoading MHJ dataset...")
    with open('mhj_dataset.json', 'r', encoding='utf-8') as f:
        mhj_data = json.load(f)

    # Extract unique base prompts
    unique_prompts = set()
    for entry in mhj_data:
        base_prompt = entry.get('base_prompt', '')
        if base_prompt:
            unique_prompts.add(base_prompt)

    print(f"Found {len(unique_prompts)} unique base prompts")

    # Check if classifications already exist
    classifications_file = Path("base_prompt_classifications.json")

    if classifications_file.exists():
        print(f"\nLoading existing classifications...")
        with open(classifications_file, 'r', encoding='utf-8') as f:
            classifications = json.load(f)
        print(f"Loaded {len(classifications)} existing classifications")
    else:
        classifications = {}

    # Find new prompts to classify
    new_prompts = unique_prompts - set(classifications.keys())

    if not new_prompts:
        print("\nAll prompts already classified!")
    else:
        print(f"\nClassifying {len(new_prompts)} new prompts...")
        print("="*60)

        for idx, prompt in enumerate(sorted(new_prompts), 1):
            print(f"\n[{idx}/{len(new_prompts)}] Classifying...")
            print(f"Prompt: {prompt[:100]}...")

            result = classifier.classify_prompt(prompt)

            classifications[prompt] = {
                'category': result['category'],
                'reasoning': result['reasoning']
            }

            print(f"Category: {result['category']}")

            # Save periodically
            if idx % 10 == 0:
                with open(classifications_file, 'w', encoding='utf-8') as f:
                    json.dump(classifications, f, indent=2, ensure_ascii=False)
                print(f"  Saved {idx} classifications...")

            # Rate limiting
            time.sleep(0.5)

    # Final save
    with open(classifications_file, 'w', encoding='utf-8') as f:
        json.dump(classifications, f, indent=2, ensure_ascii=False)

    # Generate summary
    print("\n" + "="*60)
    print("CATEGORY DISTRIBUTION")
    print("="*60)

    category_counts = {}
    for prompt, info in classifications.items():
        cat = info.get('category', 'Unknown')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Sort by count
    sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

    for category, count in sorted_cats:
        percentage = (count / len(classifications)) * 100
        print(f"{category:40s}: {count:3d} ({percentage:5.1f}%)")

    print("\n" + "="*60)
    print("CLASSIFICATION COMPLETE!")
    print(f"Total unique prompts classified: {len(classifications)}")
    print(f"Saved to: {classifications_file}")
    print("="*60)


if __name__ == "__main__":
    main()