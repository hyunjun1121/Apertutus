# GPT-4.1 StrongReject Evaluation

## Overview

This directory contains scripts for evaluating model responses using GPT-4.1 as the judge with StrongReject methodology.

## Two Evaluation Approaches

### 1. English Template Evaluation (`run_strongreject_gpt_parallel.py`)
- Uses **English StrongReject template** for all languages
- Evaluates model responses using the original English rubric
- Output: `final_results/gpt_english_eval/{language}_gpt_english_eval.json`

### 2. Translated Template Evaluation (`run_strongreject_gpt_translated.py`)
- Uses **translated StrongReject template** for each language
- Evaluates model responses using the native language rubric
- Output: `final_results/gpt_translated_eval/{language}_gpt_translated_eval.json`

## Configuration

- **Model**: `openai/gpt-4.1`
- **API**: Custom endpoint at `http://5.78.122.79:10000/v1`
- **Workers**: 40 parallel workers (configurable)
- **Temperature**: 0.1
- **Max Tokens**: 1000

## Data Split

Each script automatically splits the dataset into 40 chunks to avoid duplication:
- Each language file is divided into 40 equal chunks
- Each worker processes one chunk independently
- Results are combined and sorted by entry_index

## Usage

### Run English Template Evaluation
```bash
python run_strongreject_gpt_parallel.py --workers 40
```

### Run Translated Template Evaluation
```bash
python run_strongreject_gpt_translated.py --workers 40
```

### Run Both in Parallel (separate terminals)
```bash
# Terminal 1
python run_strongreject_gpt_parallel.py --workers 40

# Terminal 2
python run_strongreject_gpt_translated.py --workers 40
```

## Output Format

Each evaluation file contains:
```json
[
  {
    "entry_index": 0,
    "gpt_english_evaluation": {
      "refused": 1,
      "convincing_score": 5,
      "specific_score": 4,
      "strongreject_score": 0.0,
      "raw_response": "..."
    }
  }
]
```

or

```json
[
  {
    "entry_index": 0,
    "gpt_translated_evaluation": {
      "refused": 1,
      "convincing_score": 5,
      "specific_score": 3,
      "strongreject_score": 0.0,
      "raw_response": "..."
    }
  }
]
```

## No Overlap with Existing Apertus Results

- Existing Apertus evaluations are in: `final_results/*_complete.json`
- GPT English evaluations go to: `final_results/gpt_english_eval/`
- GPT Translated evaluations go to: `final_results/gpt_translated_eval/`

These are completely separate directories, ensuring no conflicts.

## Languages Supported

All 16 languages:
- arb.Arab (Arabic)
- ces.Latn (Czech)
- cmn.Hani (Chinese)
- deu.Latn (German)
- fra.Latn (French)
- ind.Latn (Indonesian)
- ita.Latn (Italian)
- jpn.Jpan (Japanese)
- kor.Hang (Korean)
- nld.Latn (Dutch)
- pol.Latn (Polish)
- por.Latn (Portuguese)
- ron.Latn (Romanian)
- rus.Cyrl (Russian)
- spa.Latn (Spanish)
- tur.Latn (Turkish)

## Performance

With 40 parallel workers:
- Expected processing time: ~10-15 minutes per evaluation type
- Total entries: 16 languages × 382 entries = 6,112 entries
- Rate: ~10-15 entries/second
