# StrongReject Evaluation with Multiple Judges

## Overview

This directory contains scripts for evaluating model responses using different judge models with StrongReject methodology.

## Three Evaluation Approaches

### 1. GPT-4.1 + English Template (`run_strongreject_gpt_parallel.py`)
- **Judge Model**: GPT-4.1
- **Template**: English StrongReject template for all languages
- **Output**: `final_results/gpt_english_eval/{language}_gpt_english_eval.json`

### 2. GPT-4.1 + Translated Template (`run_strongreject_gpt_translated.py`)
- **Judge Model**: GPT-4.1
- **Template**: Translated StrongReject template (native language)
- **Output**: `final_results/gpt_translated_eval/{language}_gpt_translated_eval.json`

### 3. Apertus-70B + Translated Template (`run_strongreject_apertus_translated.py`)
- **Judge Model**: Apertus-70B
- **Template**: Translated StrongReject template (native language)
- **Output**: `final_results/apertus_translated_eval/{language}_apertus_translated_eval.json`

## Configuration

### GPT-4.1 Scripts
- **Model**: `openai/gpt-4.1`
- **API**: Custom endpoint at `http://5.78.122.79:10000/v1`
- **Workers**: 40 parallel workers (configurable)
- **Temperature**: 0.1
- **Max Tokens**: 1000

### Apertus-70B Script
- **Model**: Apertus-70B
- **API**: Swiss AI endpoint (via config.json)
- **Workers**: 40 parallel workers (configurable)
- **Temperature**: 0.1
- **Max Tokens**: 1000

## Data Split

Each script automatically splits the dataset into 40 chunks to avoid duplication:
- Each language file is divided into 40 equal chunks
- Each worker processes one chunk independently
- Results are combined and sorted by entry_index

## Usage

### Run Individual Scripts

```bash
# GPT-4.1 + English Template
python3 run_strongreject_gpt_parallel.py --workers 40

# GPT-4.1 + Translated Template
python3 run_strongreject_gpt_translated.py --workers 40

# Apertus-70B + Translated Template
python3 run_strongreject_apertus_translated.py --workers 40
```

### Run All Three in Parallel (using tmux)

```bash
bash run_both_evaluations.sh
```

This creates 3 tmux sessions:
- `gpt_english`: GPT-4.1 with English template
- `gpt_translated`: GPT-4.1 with translated template
- `apertus_translated`: Apertus-70B with translated template

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

## No Overlap with Existing Results

All evaluations are saved in separate directories:
- **Original Apertus (English)**: `final_results/*_complete.json`
- **GPT-4.1 + English**: `final_results/gpt_english_eval/`
- **GPT-4.1 + Translated**: `final_results/gpt_translated_eval/`
- **Apertus-70B + Translated**: `final_results/apertus_translated_eval/`

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
