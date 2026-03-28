# Kosovo NLP — EU Progress Report Scoring

Dictionary-based criticism scoring of EU Enlargement Progress Reports for Western Balkans countries. Follows the EPU methodology (Baker, Bloom & Davis 2016): keyword hits normalized per 1,000 words.

---

## Directory layout

```
kosovo-nlp/
│
├── dictionary.py          # Vocabulary lists + dict_score() function
├── corpus.py              # Paragraph extraction & standardization
├── score.py               # Paragraph scoring + country-year aggregation
├── pipeline.py            # CLI end-to-end runner
├── pipeline.ipynb         # Interactive notebook demo
│
├── scraped/
│   └── raw/               # {country}_{year}_raw.txt  (PDF → text, one per report)
│
├── data/                  # Generated outputs (git-ignored)
│   ├── paragraphs.csv     # Paragraph corpus (29K+ rows)
│   ├── scores.csv         # Paragraph-level scores
│   └── summary.csv        # Country-year aggregated scores
│
├── eu_reports/            # PDF scraping utilities
│   ├── scrape_raw.py      # PDF → raw .txt  (uses PyMuPDF)
│   ├── scrape_eu.py       # Extract sections 1.1/1.2 from PDFs
│   └── scrape_anchors.py  # Sentence-level topic segmentation
│
└── preprocess.py          # DEPRECATED — page-level scoring (use corpus.py + score.py)
```

---

## Pipeline

```
PDF files
   │
   ▼  eu_reports/scrape_raw.py
scraped/raw/{country}_{year}_raw.txt
   │
   ▼  corpus.py  build_corpus()
data/paragraphs.csv       country | year | paragraph_id | paragraph_text | word_count
   │
   ▼  score.py  score_corpus()
data/scores.csv           + criticism_hard_p1k | criticism_soft_p1k | severity_ratio
   │
   ▼  score.py  aggregate_country_year()
data/summary.csv          country | year | *_uw | *_ww  (unweighted + word-weighted)
```

---

## Quickstart

```bash
# 1. Extract paragraphs from all raw reports
python corpus.py

# 2. Score paragraphs and aggregate
python score.py

# 3. Or run both steps at once
python pipeline.py
```

Or open `pipeline.ipynb` to run the full pipeline interactively with plots.

---

## Module reference

### `dictionary.py`
Defines four vocabulary lists and the core scoring function.

- `CRITICISM_HARD` — explicit failure/regression language ("failed", "backsliding", "violation")
- `CRITICISM_SOFT` — hedged concern language ("concern", "challenge", "delayed")
- `REFORM_HARD` — confirmed completed achievements ("adopted", "implemented", "established")
- `REFORM_SOFT` — effort/intent without delivery ("progress", "improving", "working towards")
- `TOPICS` — topic-keyed vocabulary sets: `judiciary`, `corruption`, `governance`, `economy`
- `dict_score(text, term_list)` → `(raw_count, per_1000_words)`

### `corpus.py`
Turns raw `.txt` files into a standardized paragraph DataFrame.

- `build_corpus(raw_dir, min_words=50, max_words=500)` → DataFrame
- `extract_paragraphs(text)` — handles two PDF extraction formats via dual boundary signals
- `split_long(text, max_words)` — splits oversized paragraphs at sentence boundaries

### `score.py`
Scores a paragraph DataFrame and aggregates to country-year level.

- `score_corpus(df)` → df with `criticism_hard_p1k`, `criticism_soft_p1k`, `severity_ratio`
- `aggregate_country_year(df_scored)` → country-year summary with `_uw` (unweighted) and `_ww` (word-weighted) columns

### `pipeline.py`
End-to-end CLI runner chaining `build_corpus → score_corpus → aggregate_country_year`.

```
python pipeline.py --raw-dir scraped/raw \
                   --paragraphs data/paragraphs.csv \
                   --scores data/scores.csv \
                   --summary data/summary.csv
```

---

## Data schema

### `paragraphs.csv`
| Column | Type | Description |
|---|---|---|
| `country` | str | Country name (title case) |
| `year` | int | Report year |
| `paragraph_id` | int | Per-document paragraph index |
| `paragraph_text` | str | Cleaned paragraph text |
| `word_count` | int | Word count (50–500 after standardization) |

### `scores.csv`
All columns from `paragraphs.csv` plus:

| Column | Type | Description |
|---|---|---|
| `criticism_hard_p1k` | float | Hard criticism hits per 1,000 words |
| `criticism_soft_p1k` | float | Soft criticism hits per 1,000 words |
| `severity_ratio` | float | `hard_p1k / soft_p1k`  (NaN when soft = 0) |

### `summary.csv`
| Column | Description |
|---|---|
| `country`, `year` | Aggregation keys |
| `criticism_hard_p1k_uw` | Unweighted mean hard criticism across paragraphs |
| `criticism_hard_p1k_ww` | Word-count weighted mean hard criticism |
| `criticism_soft_p1k_uw/ww` | Same for soft criticism |
| `severity_ratio_uw/ww` | Same for severity ratio |

---

## Dictionary methodology

Scores follow the EPU framework: for each paragraph, count substring hits (lowercased) from each vocabulary list, normalize by word count × 1,000.

**Hard criticism** (`criticism_hard_p1k`): EU is explicitly condemning failure or regression. Rare but high-signal (e.g. "backsliding", "violation", "state capture").

**Soft criticism** (`criticism_soft_p1k`): EU is flagging concern or noting challenges — hedged, not condemning. Common in all reports (e.g. "concern", "challenge", "limited progress").

**Severity ratio** (`severity_ratio = hard / soft`): A high ratio means the EU is explicitly condemning rather than just flagging. Undefined (NaN) when soft = 0.
