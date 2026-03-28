"""
preprocess.py — EU Progress Report text cleaning pipeline

Two-phase cleaning + paragraph extraction.

  clean_text(text)       → lowercased body text ready for dict_score()
  get_paragraphs(text)   → list of (paragraph_text, is_header) tuples
                           for chunk-level or section-level scoring
  cleaning_report(text)  → diagnostic word-count breakdown

Phase 1 (structural) — applied to original-case text:
  - Numbered and ALL-CAPS section headers
  - "Chapter XX:" headers (chapter-based format, 2024+)
  - Page numbers, *** dividers
  - → arrow bullet prefix (content kept, symbol stripped)

Phase 2 (boilerplate) — applied after lowercasing:
  - Assessment scale footnote (appears in every report)
  - "Commission's recommendations from last year" transition sentence
  - "In the coming year, [country] should/needs, in particular:" lead-in
  - Footnote reference superscripts mid-word

Why two phases?
  Headers require case-sensitive matching (ALL CAPS can't be detected
  after lowercasing). Boilerplate phrases are matched case-insensitively.

Usage:
    from preprocess import clean_text, get_paragraphs, cleaning_report
"""

import re

_ARROW = '\u2192'  # → U+2192, used as bullet in chapter-based reports (2024+)

# ---------------------------------------------------------------------------
# Phase 1: structural patterns (matched on original-case text)
# ---------------------------------------------------------------------------
_STRUCTURAL: list[tuple[str, int]] = [
    # ===== PAGE N ===== markers (present in raw files from scrape_raw.py)
    (r'^={3,}[^\n]*={3,}$', re.MULTILINE),

    # Table of contents dot-leader lines: "Chapter 23 ......... 25"
    (r'^[^\n]+\.{4,}\s*\d+\s*$', re.MULTILINE),

    # *** section dividers
    (r'\*\s*\*\s*\*', re.MULTILINE),

    # Lone page numbers (single number on its own line)
    (r'^\s*\d{1,3}\s*$', re.MULTILINE),

    # Numbered ALL-CAPS headers: "1. INTRODUCTION", "1.1. CONTEXT", "1.2 MAIN FINDINGS"
    # (the existing notebook pattern was applied post-lowercase so it never matched)
    (r'^\s*\d+\.?\d*\.?\s+[A-Z][A-Z\s\-]+\s*$', re.MULTILINE),

    # "Chapter XX: Title" — chapter-based format (2024+)
    (r'^[Cc]hapter\s+\d+[:\s][^\n]*$', re.MULTILINE),

    # Standalone ALL-CAPS section titles, e.g. "THE FUNDAMENTALS OF THE ACCESSION PROCESS"
    # Require 15+ chars to avoid killing legitimate short abbreviations
    (r'^[A-Z][A-Z\s\/\-]{14,}$', re.MULTILINE),

    # Strip the → prefix character itself but keep the sentence content.
    # The recommendation text is genuine analytical signal ("Kosovo needs to adopt...",
    # "strengthen the judiciary...") — only the bullet symbol is noise.
    (_ARROW, 0),
]

# ---------------------------------------------------------------------------
# Phase 2: boilerplate patterns (matched on lowercased text)
# ---------------------------------------------------------------------------
# NOTE: do NOT use re.DOTALL on patterns that match single sentences — with
# DOTALL and a non-greedy .*? the regex will skip to the next occurrence of
# the terminal string elsewhere in the document, consuming huge blocks of text.
_BOILERPLATE: list[tuple[str, int]] = [
    # Fixed assessment scale footnote (every report, contains dictionary words).
    # This spans multiple sentences so DOTALL is intentional here.
    (r'the report uses the following assessment scale.*?interim steps have also been used\.?',
     re.MULTILINE | re.DOTALL),

    # Report period footnote (variant phrasing in older reports). Also multi-sentence.
    (r'this report covers the period from.*?in particular in the area of rule of law\.?',
     re.MULTILINE | re.DOTALL),

    # "The Commission's recommendations from last year were [not] implemented and remain
    # [largely] valid." — phrasing varies slightly by year; keep to a single line.
    (r"the commission.s recommendations from last year[^\n]*\.", re.MULTILINE),

    # "In the coming year, [country] should/needs[, in particular[, to]]:"
    # Single sentence — no DOTALL. Handles both ": " and ", to:" variants.
    (r'in the coming year,\s+\w[\w\s,]+(?:should|needs|need to)[^\n]*', re.MULTILINE),

    # Inline footnote reference numbers, e.g. "Kosovo2 has" → "Kosovo has"
    (r'(?<=\w)\d{1,2}(?=[\s,.])', 0),
]


def clean_text(text: str) -> str:
    """
    Full two-phase cleaning pipeline.
    Returns lowercased, whitespace-normalised body text ready for dict_score().
    """
    # Phase 1: strip structural noise (must run before lowercasing)
    for pattern, flags in _STRUCTURAL:
        text = re.sub(pattern, ' ', text, flags=flags)

    # Phase 2: lowercase then strip boilerplate phrases
    t = text.lower()
    for pattern, flags in _BOILERPLATE:
        t = re.sub(pattern, ' ', t, flags=flags)

    return re.sub(r'\s+', ' ', t).strip()


def cleaning_report(raw: str) -> dict:
    """
    Diagnostic: returns word counts at each cleaning stage.
    Useful for auditing how much text each phase removes per document.

    Example output:
        {'raw_words': 6766, 'after_structural': 5201, 'final_words': 5050,
         'structural_removed': 1565, 'boilerplate_removed': 151,
         'total_removed': 1716, 'pct_removed': 25.4}
    """
    after_structural = raw
    for pattern, flags in _STRUCTURAL:
        after_structural = re.sub(pattern, ' ', after_structural, flags=flags)

    t = after_structural.lower()
    for pattern, flags in _BOILERPLATE:
        t = re.sub(pattern, ' ', t, flags=flags)
    final = re.sub(r'\s+', ' ', t).strip()

    raw_w        = len(raw.split())
    struct_w     = len(after_structural.split())
    final_w      = len(final.split())

    return {
        'raw_words':          raw_w,
        'after_structural':   struct_w,
        'final_words':        final_w,
        'structural_removed': raw_w - struct_w,
        'boilerplate_removed': struct_w - final_w,
        'total_removed':      raw_w - final_w,
        'pct_removed':        round(100 * (raw_w - final_w) / raw_w, 1) if raw_w else 0,
    }


# ---------------------------------------------------------------------------
# Header detection helper (used by get_paragraphs)
# ---------------------------------------------------------------------------
_HEADER_RE = re.compile(
    r'^\s*('
    r'\d+\.?\d*\.?\s+[A-Z][A-Z\s\-]+'           # "1.1 CONTEXT", "1.2 MAIN FINDINGS"
    r'|[Cc]hapter\s+\d+[:\s].*'                  # "Chapter 23: Judiciary..."
    r'|[A-Z][A-Z\s\/\-]{14,}'                    # ALL-CAPS titles 15+ chars
    r'|\*\s*\*\s*\*'                              # *** dividers
    r')\s*$'
)

_PAGE_MARKER_RE = re.compile(r'^={3,}.*?={3,}$', re.MULTILINE)


def get_paragraphs(text: str, min_words: int = 8) -> list[dict]:
    """
    Split a corpus document into paragraphs with structural labels.

    Works on both raw files (with ===== PAGE N ===== markers) and pre-processed
    corpus files. Corpus files use single newlines (word-wrap), not double newlines,
    so this function scans line-by-line: header lines flush the current paragraph
    accumulator, blank lines act as soft separators.

    Returns a list of dicts, each with:
      'text'      — cleaned paragraph text (lowercased, whitespace-normalised)
      'raw_text'  — original paragraph text before lowercasing
      'is_header' — True if the paragraph looks like a section header
      'n_words'   — word count of cleaned text

    Paragraphs with fewer than min_words words are dropped (page artefacts,
    stray punctuation, lone page numbers, etc.).

    Typical notebook usage — score body paragraphs only:

        paras    = get_paragraphs(raw_text)
        body     = [p for p in paras if not p['is_header']]
        combined = ' '.join(p['text'] for p in body)
        _, ch_p1k = dict_score(combined, CRITICISM_HARD)
    """
    # Strip page markers (present in raw files, harmless if absent in corpus files)
    text = _PAGE_MARKER_RE.sub('\n', text)
    # Strip → prefix (keep sentence content)
    text = text.replace(_ARROW, ' ')

    def _emit(lines: list[str], is_header: bool) -> dict | None:
        raw = ' '.join(lines).strip()
        if not raw:
            return None
        cleaned = re.sub(r'\s+', ' ', raw.lower()).strip()
        n = len(cleaned.split())
        if n < min_words:
            return None
        return {'raw_text': raw, 'text': cleaned, 'is_header': is_header, 'n_words': n}

    paragraphs: list[dict] = []
    accumulator: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        # Blank line → flush accumulator as body paragraph
        if not stripped:
            if accumulator:
                p = _emit(accumulator, is_header=False)
                if p:
                    paragraphs.append(p)
                accumulator = []
            continue

        # Lone page number → discard
        if re.match(r'^\d{1,3}$', stripped):
            continue

        # Header line → flush accumulator, then emit header as its own entry
        if _HEADER_RE.match(stripped):
            if accumulator:
                p = _emit(accumulator, is_header=False)
                if p:
                    paragraphs.append(p)
                accumulator = []
            p = _emit([stripped], is_header=True)
            if p:
                paragraphs.append(p)
            continue

        accumulator.append(stripped)

    # Flush any remaining lines
    if accumulator:
        p = _emit(accumulator, is_header=False)
        if p:
            paragraphs.append(p)

    return paragraphs
