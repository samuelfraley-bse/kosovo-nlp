"""
scrape_raw.py
-------------
Dumps the full text of every EU Enlargement report PDF into
  ../scraped/raw/{country}_{year}_raw.txt

Each page is separated by a marker:
  ===== PAGE 4 =====
so the notebook can reference exact locations if needed.

Run from the eu_reports/ directory:
    python scrape_raw.py
"""

import fitz   # PyMuPDF
import os
import re
import glob

output_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "scraped", "raw"))
os.makedirs(output_dir, exist_ok=True)

# Matches both naming conventions in the folder:
#   albania-report-2024.pdf
#   kosovo_report_2020.pdf  (underscore variant)
pdf_files = glob.glob("*report*.pdf") + glob.glob("*report*.PDF")
pdf_files = list(set(pdf_files))   # deduplicate

print(f"🚀  Found {len(pdf_files)} PDFs  →  {output_dir}\n")

for filename in sorted(pdf_files):
    # Parse country + year from filename regardless of separator style
    clean = filename.lower().replace(".pdf", "")
    parts = re.split(r"[-_]", clean)

    year_idx = next((i for i, p in enumerate(parts) if re.fullmatch(r"\d{4}", p)), None)
    if year_idx is None:
        print(f"  ⚠  Cannot parse year from {filename}, skipping.")
        continue

    # Country slug = everything before "report" token
    try:
        report_idx = parts.index("report")
        country = "_".join(parts[:report_idx])
    except ValueError:
        country = "_".join(parts[:year_idx])

    year = parts[year_idx]

    out_path = os.path.join(output_dir, f"{country}_{year}_raw.txt")

    try:
        doc   = fitz.open(filename)
        pages = []
        for i in range(doc.page_count):
            page_text = doc.load_page(i).get_text("text")
            pages.append(f"===== PAGE {i + 1} =====\n{page_text}")
        full_text = "\n\n".join(pages)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"  ✅  {filename}  →  {country}_{year}_raw.txt  ({doc.page_count} pages, {len(full_text.split())} words)")
        doc.close()

    except Exception as e:
        print(f"  ❌  {filename}: {e}")

print("\n✨  Done.")
