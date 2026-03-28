# Kosovo NLP

Dictionary-based NLP workflow for analysing criticism in EU Progress Reports, centered on [`notebooks/final_pipeline.ipynb`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/notebooks/final_pipeline.ipynb).

The repository builds a paragraph-level corpus from scraped EU reports, scores each paragraph with a custom criticism dictionary, aggregates results to the country-year level, tags policy topics, and runs the final regression/visual analysis in the notebook.

## Main entry point

The project is now organized around [`notebooks/final_pipeline.ipynb`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/notebooks/final_pipeline.ipynb).

That notebook is the end-to-end research workflow:

1. Builds the paragraph corpus from raw text files in `scraped/raw/`
2. Scores paragraphs using the hard/soft criticism dictionaries
3. Aggregates results to country-year level
4. Tags paragraphs by policy topic
5. Runs the final regression specification
6. Produces the main maps and figures used for interpretation

If you only open one file in this repo, open [`notebooks/final_pipeline.ipynb`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/notebooks/final_pipeline.ipynb).

## Current repository structure

```text
kosovo_nlp/
|-- notebooks/
|   |-- final_pipeline.ipynb      # Main analysis notebook
|   `-- adhoc/                    # Older exploratory or scratch notebooks
|
|-- src/
|   |-- corpus.py                 # Build paragraph corpus from raw report text
|   |-- dictionary.py             # Custom lexicon and dictionary scoring helpers
|   |-- pipeline.py               # Script wrapper for corpus -> score -> summary
|   |-- preprocess.py             # Older preprocessing utilities
|   |-- score.py                  # Paragraph scoring, topic tagging, aggregation
|   |-- scrape.py                 # Scraping-related helper script
|   `-- scrape_un.py              # UN scraping-related helper script
|
|-- data/
|   |-- paragraphs.csv            # Paragraph-level corpus output
|   |-- scores.csv                # Paragraph-level scoring output
|   `-- summary.csv               # Country-year summary output
|
|-- scraped/                      # Raw scraped text inputs
|-- eu_reports/                   # EU report scraping and earlier report-analysis utilities
|-- main.py                       # Minimal project entry script
|-- pyproject.toml                # Project metadata and dependencies
|-- uv.lock                       # Locked dependency set
`-- README.md
```

## Workflow

### Notebook-first workflow

The intended workflow is:

1. Open [`notebooks/final_pipeline.ipynb`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/notebooks/final_pipeline.ipynb)
2. Run the notebook top to bottom
3. Use the generated `df`, scored data, aggregated tables, regression outputs, and plots directly in the notebook

The notebook already includes repo-root detection so it can find `src/` even if the kernel starts from the `notebooks/` directory.

### Script workflow

If you want to reproduce the intermediate CSVs outside the notebook, the core script is [`src/pipeline.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/pipeline.py).

```bash
python src/pipeline.py
```

This runs:

1. [`src/corpus.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/corpus.py) to create `data/paragraphs.csv`
2. [`src/score.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/score.py) to create `data/scores.csv`
3. Aggregation to create `data/summary.csv`

You can also run stages individually:

```bash
python src/corpus.py
python src/score.py
python src/pipeline.py
```

## Core modules

[`src/corpus.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/corpus.py)
Builds the paragraph-level corpus from `*_raw.txt` files. It removes page markers, detects paragraph boundaries, filters out short fragments, and splits very long paragraphs.

[`src/dictionary.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/dictionary.py)
Defines the criticism dictionaries and scoring helpers used throughout the project.

[`src/score.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/score.py)
Applies dictionary scoring, computes `criticism_hard_p1k`, `criticism_soft_p1k`, and `severity_ratio`, tags topic areas, and aggregates to the country-year level.

[`src/pipeline.py`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/src/pipeline.py)
Convenience wrapper that runs the corpus and scoring pipeline end to end and saves the intermediate CSV outputs.

## Data outputs

[`data/paragraphs.csv`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/data/paragraphs.csv)
Paragraph-level corpus with:
`country`, `year`, `paragraph_id`, `paragraph_text`, `word_count`

[`data/scores.csv`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/data/scores.csv)
Paragraph-level scored output with the corpus columns plus:
`criticism_hard_p1k`, `criticism_soft_p1k`, `severity_ratio`

[`data/summary.csv`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/data/summary.csv)
Country-year aggregated output used in the later notebook steps.

## Other notebooks

[`notebooks/adhoc/`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/notebooks/adhoc)
Contains earlier exploratory notebooks such as raw-text EDA, EU EDA, and prior pipeline experiments. These are supporting materials, not the main workflow.

## Setup

The project uses Python 3.12+ and is configured in [`pyproject.toml`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/pyproject.toml).

If you are using `uv`:

```bash
uv sync
```

Or with standard Python tooling, install the dependencies listed in [`pyproject.toml`](/c:/Users/sffra/Downloads/BSE%202025-2026/kosovo_nlp/pyproject.toml) and then launch Jupyter to run the main notebook.
