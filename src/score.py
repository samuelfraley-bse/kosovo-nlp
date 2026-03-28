"""
score.py — Paragraph-level scoring and country-year aggregation.

Applies the criticism dictionary to a paragraph DataFrame and aggregates
results to country-year level using both unweighted and word-count weighted means.

Usage:
  python score.py                                   # reads data/paragraphs.csv
  python score.py --corpus data/paragraphs.csv --out data/scores.csv --summary data/summary.csv
"""

import argparse
from pathlib import Path

import pandas as pd

from dictionary import CRITICISM_HARD, CRITICISM_SOFT, TOPICS, dict_score

METRICS     = ["criticism_hard_p1k", "criticism_soft_p1k", "severity_ratio"]
TOPIC_COLS  = [f"topic_{t}" for t in TOPICS]


def score_corpus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score every paragraph in df and return a copy with three new columns:
      criticism_hard_p1k  — hard criticism hits per 1,000 words
      criticism_soft_p1k  — soft criticism hits per 1,000 words
      severity_ratio      — hard_p1k / soft_p1k  (NaN when soft = 0)
    """
    def _score_row(text: str) -> tuple[float, float, float]:
        _, hard_p1k = dict_score(text, CRITICISM_HARD)
        _, soft_p1k = dict_score(text, CRITICISM_SOFT)
        severity    = hard_p1k / soft_p1k if soft_p1k > 0 else float("nan")
        return hard_p1k, soft_p1k, severity

    scores = df["paragraph_text"].apply(
        lambda t: pd.Series(_score_row(t), index=METRICS)
    )
    return pd.concat([df, scores], axis=1)


def aggregate_country_year(df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate paragraph scores to country-year level.

    Returns the unweighted mean across paragraphs for each metric.
    p1k normalisation already accounts for paragraph length, so
    additional word-count weighting is redundant.
    """
    return (
        df_scored
        .groupby(["country", "year"])[METRICS]
        .mean()
        .round(4)
        .reset_index()
    )


def tag_topics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add one boolean column per topic (e.g. topic_judiciary_rule_of_law).
    True when any term from that topic's list appears in the paragraph text.
    A paragraph can be True for multiple topics simultaneously.
    """
    df = df.copy()
    for topic, terms in TOPICS.items():
        col = f"topic_{topic}"
        df[col] = df["paragraph_text"].str.lower().apply(
            lambda text: any(term in text for term in terms)
        )
    return df


def aggregate_by_topic(df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    For each topic, filter to paragraphs flagged for that topic and compute
    country-year criticism scores (unweighted mean).

    Returns a long-format DataFrame:
      country | year | topic | n_paragraphs |
      criticism_hard_p1k | criticism_soft_p1k | severity_ratio
    """
    rows = []
    for topic in TOPICS:
        col = f"topic_{topic}"
        if col not in df_scored.columns:
            continue
        subset = df_scored[df_scored[col]]
        for (country, year), g in subset.groupby(["country", "year"]):
            row = {"country": country, "year": year, "topic": topic, "n_paragraphs": len(g)}
            for m in METRICS:
                row[m] = round(g[m].mean(), 4)
            rows.append(row)

    cols = ["country", "year", "topic", "n_paragraphs"] + METRICS
    return pd.DataFrame(rows, columns=cols)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus",  default="data/paragraphs.csv", help="Paragraph corpus CSV")
    parser.add_argument("--out",     default="data/scores.csv",     help="Paragraph-level scored output")
    parser.add_argument("--summary", default="data/summary.csv",    help="Country-year aggregated output")
    args = parser.parse_args()

    print(f"Loading corpus from {args.corpus} …")
    df = pd.read_csv(args.corpus)

    print(f"Scoring {len(df):,} paragraphs …")
    df_scored = score_corpus(df)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df_scored.to_csv(out, index=False)
    print(f"Paragraph scores saved → {out}")

    summary = aggregate_country_year(df_scored)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    print(f"Country-year summary saved → {args.summary}")
    print(f"\n{summary.to_string(index=False)}")
