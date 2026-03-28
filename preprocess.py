"""
DEPRECATED: page-level scoring, superseded by corpus.py + score.py (paragraph-level pipeline).

Simple preprocessing pipeline for EU progress report raw text files.

Loads a scraped .txt file, splits into page-level chunks, and scores each
chunk using the criticism/reform dictionary (CRITICISM_HARD, CRITICISM_SOFT).

Derived scores per chunk:
  criticism_hard_p1k  — hard criticism hits per 1,000 words
  criticism_soft_p1k  — soft criticism hits per 1,000 words
  severity_ratio      — hard / soft  (NaN if soft = 0)
"""

import re
import math
import pandas as pd
from pathlib import Path

from dictionary import CRITICISM_HARD, CRITICISM_SOFT, dict_score

PAGE_DELIMITER = re.compile(r"={3,}\s*PAGE\s+(\d+)\s*={3,}")


def load_chunks(path: str | Path) -> list[dict]:
    """
    Read a raw report file and return a list of page-level chunks.

    Each chunk is a dict with keys:
      page  (int), text (str), word_count (int)
    """
    text = Path(path).read_text(encoding="utf-8")

    parts = PAGE_DELIMITER.split(text)
    # split returns: [pre-text, page_num, page_body, page_num, page_body, ...]
    # parts[0] is content before the first delimiter (usually empty)

    chunks = []
    i = 1
    while i + 1 < len(parts):
        page_num = int(parts[i])
        body = parts[i + 1].strip()
        word_count = len(body.split())
        if word_count > 0:
            chunks.append({"page": page_num, "text": body, "word_count": word_count})
        i += 2

    return chunks


def score_chunks(chunks: list[dict]) -> pd.DataFrame:
    """
    Score a list of page chunks and return a DataFrame.

    Columns:
      page, word_count,
      criticism_hard_raw, criticism_hard_p1k,
      criticism_soft_raw, criticism_soft_p1k,
      severity_ratio
    """
    rows = []
    for chunk in chunks:
        hard_raw, hard_p1k = dict_score(chunk["text"], CRITICISM_HARD)
        soft_raw, soft_p1k = dict_score(chunk["text"], CRITICISM_SOFT)

        severity = hard_p1k / soft_p1k if soft_p1k > 0 else float("nan")

        rows.append(
            {
                "page": chunk["page"],
                "word_count": chunk["word_count"],
                "criticism_hard_raw": hard_raw,
                "criticism_hard_p1k": round(hard_p1k, 4),
                "criticism_soft_raw": soft_raw,
                "criticism_soft_p1k": round(soft_p1k, 4),
                "severity_ratio": round(severity, 4) if not math.isnan(severity) else float("nan"),
            }
        )

    return pd.DataFrame(rows)


def preprocess_report(path: str | Path) -> pd.DataFrame:
    """
    Full pipeline: load → chunk → score.
    Returns a scored DataFrame for a single report file.
    """
    chunks = load_chunks(path)
    return score_chunks(chunks)


# ---------------------------------------------------------------------------
# Quick smoke-test when run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    report_path = sys.argv[1] if len(sys.argv) > 1 else "scraped/raw/kosovo_2024_raw.txt"
    df = preprocess_report(report_path)

    print(f"Loaded {len(df)} pages from {report_path}\n")
    print(df.to_string(index=False))
    print(f"\nDocument-level summary:")
    print(f"  Total words          : {df['word_count'].sum():,}")
    print(f"  Criticism hard (raw) : {df['criticism_hard_raw'].sum()}")
    print(f"  Criticism soft (raw) : {df['criticism_soft_raw'].sum()}")
    doc_hard = df["criticism_hard_raw"].sum() / df["word_count"].sum() * 1000
    doc_soft = df["criticism_soft_raw"].sum() / df["word_count"].sum() * 1000
    print(f"  Criticism hard p1k   : {doc_hard:.4f}")
    print(f"  Criticism soft p1k   : {doc_soft:.4f}")
    print(f"  Severity ratio       : {doc_hard / doc_soft:.4f}" if doc_soft > 0 else "  Severity ratio       : N/A")
