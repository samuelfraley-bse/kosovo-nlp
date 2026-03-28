"""
corpus.py — Paragraph extraction and standardization.

Turns raw EU progress report .txt files into a clean paragraph-level DataFrame.

Output schema:
  country | year | paragraph_id | paragraph_text | word_count

Usage:
  python corpus.py                        # writes data/paragraphs.csv
  python corpus.py --out my_output.csv
  python corpus.py --min-words 50 --max-words 500
"""

import re
import argparse
from pathlib import Path

import pandas as pd

RAW_DIR   = Path("scraped/raw")
PAGE_RE   = re.compile(r"={3,}\s*PAGE\s+\d+\s*={3,}")
FILE_RE   = re.compile(r"^(.+?)_(\d{4})_raw\.txt$")

MIN_WORDS_DEFAULT = 50
MAX_WORDS_DEFAULT = 500


def parse_filename(name: str) -> tuple[str, int] | tuple[None, None]:
    """Extract (country, year) from e.g. 'north_macedonia_2024_raw.txt'."""
    m = FILE_RE.match(name)
    if not m:
        return None, None
    country = m.group(1).replace("_", " ").title()
    year    = int(m.group(2))
    return country, year


def extract_paragraphs(text: str) -> list[str]:
    """
    Detect paragraph boundaries and return a list of raw paragraph strings.

    Two boundary signals exist across scraped files:
      1. Double trailing space + newline  (Kosovo, Albania, Montenegro …)
      2. Sentence-end + single space + newline + capital/bullet  (North Macedonia, Serbia …)
    Both are normalised to \\n\\n before splitting.
    """
    text = PAGE_RE.sub("", text)

    # Signal 1: double trailing space + newline
    text = re.sub(r"  \n", "\n\n", text)

    # Signal 2: word(4+ chars) ending sentence + single space + newline + capital/bullet
    # Minimum 4-char word avoids splitting on abbreviations (Mr. Dr. vs. etc.)
    text = re.sub(r"([A-Za-z]{4,}[.!?]) \n(?=[A-Z→])", r"\1\n\n", text)

    chunks = re.split(r"\n{2,}", text)
    return [c.replace("\n", " ").strip() for c in chunks]


def split_long(text: str, max_words: int = MAX_WORDS_DEFAULT) -> list[str]:
    """Split a paragraph exceeding max_words at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], []
    for sent in sentences:
        current.append(sent)
        if len(" ".join(current).split()) >= max_words:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def build_corpus(
    raw_dir: str | Path = RAW_DIR,
    min_words: int = MIN_WORDS_DEFAULT,
    max_words: int = MAX_WORDS_DEFAULT,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Process all *_raw.txt files in raw_dir and return a paragraph DataFrame.

    Parameters
    ----------
    raw_dir   : directory containing *_raw.txt files
    min_words : drop paragraphs shorter than this (removes headers/noise)
    max_words : split paragraphs longer than this at sentence boundaries
    verbose   : print per-file paragraph counts
    """
    raw_dir = Path(raw_dir)
    rows = []

    for path in sorted(raw_dir.glob("*_raw.txt")):
        country, year = parse_filename(path.name)
        if country is None:
            if verbose:
                print(f"  [skip] cannot parse: {path.name}")
            continue

        text       = path.read_text(encoding="utf-8")
        candidates = extract_paragraphs(text)

        para_id = 0
        for p in candidates:
            wc = len(p.split())
            if wc < min_words:
                continue
            sub_paras = split_long(p, max_words) if wc > max_words else [p]
            for sub in sub_paras:
                sub_wc = len(sub.split())
                if sub_wc < min_words:
                    continue
                rows.append({
                    "country":        country,
                    "year":           year,
                    "paragraph_id":   para_id,
                    "paragraph_text": sub,
                    "word_count":     sub_wc,
                })
                para_id += 1

        if verbose:
            print(f"  {country:<25} {year}  →  {para_id} paragraphs")

    return pd.DataFrame(
        rows,
        columns=["country", "year", "paragraph_id", "paragraph_text", "word_count"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir",   default=str(RAW_DIR),        help="Directory of raw .txt files")
    parser.add_argument("--out",       default="data/paragraphs.csv", help="Output CSV path")
    parser.add_argument("--min-words", type=int, default=MIN_WORDS_DEFAULT)
    parser.add_argument("--max-words", type=int, default=MAX_WORDS_DEFAULT)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building corpus from {args.raw_dir}  (min={args.min_words}, max={args.max_words})\n")
    df = build_corpus(args.raw_dir, args.min_words, args.max_words)

    df.to_csv(out, index=False)
    print(f"\nSaved {len(df):,} paragraphs → {out}")
    print(df["word_count"].describe().round(1).to_string())
