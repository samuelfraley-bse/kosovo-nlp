"""
pipeline.py — End-to-end runner: raw files → paragraph corpus → scores → summary.

Steps:
  1. Build paragraph corpus from scraped/raw/  (corpus.build_corpus)
  2. Score each paragraph                       (score.score_corpus)
  3. Aggregate to country-year level            (score.aggregate_country_year)
  4. Save all three outputs to data/

Usage:
  python pipeline.py
  python pipeline.py --raw-dir scraped/raw --paragraphs data/paragraphs.csv \
                     --scores data/scores.csv --summary data/summary.csv
"""

import argparse
from pathlib import Path

from corpus import build_corpus
from score  import score_corpus, aggregate_country_year


def run(
    raw_dir:    str = "scraped/raw",
    paragraphs: str = "data/paragraphs.csv",
    scores:     str = "data/scores.csv",
    summary:    str = "data/summary.csv",
) -> None:
    Path(paragraphs).parent.mkdir(parents=True, exist_ok=True)

    # Step 1 — corpus
    print("=" * 50)
    print("STEP 1 — Building paragraph corpus")
    print("=" * 50)
    df = build_corpus(raw_dir)
    df.to_csv(paragraphs, index=False)
    print(f"\n{len(df):,} paragraphs saved → {paragraphs}\n")

    # Step 2 — score
    print("=" * 50)
    print("STEP 2 — Scoring paragraphs")
    print("=" * 50)
    df_scored = score_corpus(df)
    df_scored.to_csv(scores, index=False)
    print(f"Paragraph scores saved → {scores}\n")

    # Step 3 — aggregate
    print("=" * 50)
    print("STEP 3 — Aggregating to country-year level")
    print("=" * 50)
    agg = aggregate_country_year(df_scored)
    agg.to_csv(summary, index=False)
    print(f"Country-year summary saved → {summary}\n")
    print(agg.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir",    default="scraped/raw",           help="Directory of raw .txt files")
    parser.add_argument("--paragraphs", default="data/paragraphs.csv",   help="Paragraph corpus output path")
    parser.add_argument("--scores",     default="data/scores.csv",       help="Paragraph-level scores output path")
    parser.add_argument("--summary",    default="data/summary.csv",      help="Country-year summary output path")
    args = parser.parse_args()

    run(args.raw_dir, args.paragraphs, args.scores, args.summary)
