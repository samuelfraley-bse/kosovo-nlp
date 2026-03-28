import fitz  # PyMuPDF
import os
import re
import glob

# ── Section boundary patterns (text-based, not ToC-based) ─────────────────────

# Start of section 1.1
PAT_11 = re.compile(
    r'1\.1\.?\s*\n?\s*CONTEXT',
    re.IGNORECASE
)

# Start of section 1.2 — handles all known formats:
#   "1.2. SUMMARY OF THE REPORT"
#   "1.2 SUMMARY OF THE REPORT"
#   "1.2 MAIN FINDINGS OF THE REPORT"
#   "1.2  \nSUMMARY ..."   (header split across lines)
#   "1.2  "                 (bare, Serbia/Montenegro older)
PAT_12 = re.compile(
    r'1\.2\.?\s{0,4}\n?\s{0,4}(SUMMARY|MAIN\s+FINDINGS?|)',
    re.IGNORECASE
)

# End of section 1.2 — catches all known terminators:
#   "1.3 STATE OF PLAY ..."  (Serbia / Montenegro format)
#   "CLUSTER 1"              (older EC format)
#   "THE FUNDAMENTALS OF THE ACCESSION"
#   "2. THE FUNDAMENTALS ..."
PAT_END = re.compile(
    r'(1\.3[\.\s]'
    r'|CLUSTER\s+1'
    r'|THE\s+FUNDAMENTALS\s+OF\s+THE\s+ACCESSION'
    r'|^2\.\s)',
    re.IGNORECASE | re.MULTILINE
)

# ToC patterns (still used to find the right page range)
TOC_START = re.compile(r'1\.1\.?\s*CONTEXT', re.IGNORECASE)
TOC_END   = re.compile(r'^(CLUSTER\s*1|2\.?\s+|1\.3\.?)', re.IGNORECASE)


def _strip_boilerplate(text: str) -> str:
    """Remove PDF page footers / running headers."""
    text = re.sub(r'(?i)page\s*\d+(\s+of\s+\d+)?', '', text)
    text = re.sub(r'(?i)[a-z-]+\s+\d{4}\s+report', '', text)
    return text.strip()


def extract_enlargement_corpus(pdf_path):
    """
    Extract sections 1.1 (Context) and 1.2 (Summary / Main Findings) from an
    EU Enlargement report PDF.

    Returns a string:  <section 1.1 text>  \\n\\n* * *\\n\\n  <section 1.2 text>

    Handles three structural variants seen across countries / years:
      A)  1.1 CONTEXT  →  1.2 SUMMARY  →  *** (end marker) — older EC format
      B)  1.1 CONTEXT  →  1.2 SUMMARY  →  1.3 STATE OF PLAY — Serbia / Montenegro
      C)  1.1 CONTEXT  →  1.2 MAIN FINDINGS — Kosovo 2024+ (no 1.3)
    """
    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()

        # ── Step 1: Use ToC to find a generous page window ────────────────────
        start_page = None
        end_page   = None

        for level, title, page in toc:
            t = title.strip()
            if TOC_START.search(t):
                start_page = page - 1          # convert 1-indexed → 0-indexed
            if start_page is not None and TOC_END.search(t):
                # page - 1 is the 0-indexed page where the end section begins.
                # We DON'T want to include that page, so use page - 2.
                end_page = max(start_page, page - 2)
                break

        # Fallback: scan early pages for 1.1 header text
        if start_page is None:
            for p_num in range(min(2, doc.page_count), min(12, doc.page_count)):
                if re.search(r'1\.1\.?\s*(CONTEXT)', doc.load_page(p_num).get_text(), re.IGNORECASE):
                    start_page = p_num
                    break

        if start_page is None:
            print(f"    ⚠  Could not locate section 1.1 in {os.path.basename(pdf_path)}")
            return None

        # Extract generously: up to end_page (exclusive of terminator) or +20 pages
        extract_end = (end_page + 1) if end_page else (start_page + 20)
        raw_text = ""
        for p in range(start_page, min(extract_end, doc.page_count)):
            raw_text += doc.load_page(p).get_text("text")

        # Normalise star variants
        raw_text = raw_text.replace("∗", "*").replace("* * *", "***")

        # ── Step 2: Text-based section splitting ──────────────────────────────

        m11 = PAT_11.search(raw_text)
        if not m11:
            print(f"    ⚠  1.1 pattern not found in text of {os.path.basename(pdf_path)}")
            return None

        # Find 1.2 after the 1.1 header
        m12 = PAT_12.search(raw_text, m11.end())

        if not m12:
            # No 1.2 found — check if *** already separates sections (old format
            # where the scraper was cutting here); if so, the 1.2 was already
            # removed from the PDF extract. Return just 1.1 text.
            end_of_11 = PAT_END.search(raw_text, m11.end())
            text_11   = raw_text[m11.start(): end_of_11.start() if end_of_11 else len(raw_text)]
            print(f"    ⚠  No 1.2 section found in {os.path.basename(pdf_path)} — returning 1.1 only")
            return _strip_boilerplate(text_11)

        # Find end of 1.2: explicit 1.3 / CLUSTER 1 / section 2 terminator
        end_of_12 = PAT_END.search(raw_text, m12.end() + 50)  # +50 to skip the header itself

        text_11 = raw_text[m11.start(): m12.start()]
        text_12 = raw_text[m12.start(): end_of_12.start() if end_of_12 else len(raw_text)]

        result = _strip_boilerplate(text_11) + "\n\n* * *\n\n" + _strip_boilerplate(text_12)
        return result.strip()

    except Exception as e:
        print(f"    ❌ Error processing {os.path.basename(pdf_path)}: {e}")
        return None


# ── Run ────────────────────────────────────────────────────────────────────────

# Files to (re)process. Set to None to process ALL pdfs in the folder.
# List only the specific PDFs that need re-scraping:
TARGET_FILES = [
    "kosovo-report-2024.pdf",
    "kosovo-report-2025.pdf",
    "montenegro-report-2022.pdf",
    "montenegro-report-2025.pdf",
    "serbia-report-2021.pdf",
    "serbia-report-2022.pdf",
    "serbia-report-2023.pdf",
    "serbia-report-2025.pdf",
]

output_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "scraped"))
os.makedirs(output_dir, exist_ok=True)

pdf_files = TARGET_FILES if TARGET_FILES else glob.glob("*-report-*.pdf")
# Filter to files that actually exist in the current directory
pdf_files = [f for f in pdf_files if os.path.isfile(f)]

print(f"🚀 Processing {len(pdf_files)} PDF(s) → {output_dir}\n")

for filename in pdf_files:
    clean_name = filename.lower().replace(".pdf", "")
    parts      = clean_name.split("-")
    year       = parts[-1]
    report_idx = parts.index("report") if "report" in parts else len(parts) - 1
    country    = "_".join(parts[:report_idx])

    out_filename  = f"{country}_{year}_corpus.txt"
    full_out_path = os.path.join(output_dir, out_filename)

    print(f"📄 {filename}")
    content = extract_enlargement_corpus(filename)

    if content:
        has_sep = "* * *" in content
        wc      = len(content.split())
        with open(full_out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {out_filename}  ({wc} words, separator={'yes' if has_sep else 'NO — check manually'})")
    else:
        print(f"  ❌ Extraction failed for {filename}")

print("\n✨ Done.")
