import os
import re
import csv
import time
import unicodedata
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://enlargement.ec.europa.eu"
INDEX_URL = f"{BASE}/enlargement-policy/strategy-and-reports_en"
START_YEAR = 2025
END_YEAR = 2019
OUT_DIR = "eu_reports"
METADATA_CSV = os.path.join(OUT_DIR, "downloaded_reports.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


def get_soup(session: requests.Session, url: str) -> BeautifulSoup | None:
    try:
        r = session.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except requests.RequestException:
        return None


def extract_2025_country_pages(session: requests.Session) -> dict[str, str]:
    """
    Parse the strategy/reports page and collect 2025 country report pages.
    Returns:
        {country_name: country_report_page_url}
    """
    soup = get_soup(session, INDEX_URL)
    if soup is None:
        raise RuntimeError(f"Could not load index page: {INDEX_URL}")

    country_pages = {}

    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = urljoin(BASE, a["href"])

        # Match links like "Albania Report 2025"
        if re.fullmatch(r".+ Report 2025", text) and "Communication" not in text:
            country = re.sub(r"\s+Report\s+2025$", "", text).strip()
            country_pages[country] = href

    return country_pages


def make_year_page_url(country_page_2025: str, year: int) -> str:
    """
    Convert:
      https://.../albania-report-2025_en
    to:
      https://.../albania-report-2024_en
    """
    return re.sub(r"report-\d{4}_en$", f"report-{year}_en", country_page_2025)


def find_pdf_download_url(session: requests.Session, report_page_url: str) -> str | None:
    """
    Find a PDF or download link on the report page.
    """
    soup = get_soup(session, report_page_url)
    if soup is None:
        return None

    # First try direct PDF links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(BASE, href)
        if ".pdf" in href.lower() or full.lower().endswith(".pdf"):
            return full

    # Then try links labeled Download
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True).lower()
        if "download" in text:
            return urljoin(BASE, a["href"])

    return None


def download_file(session: requests.Session, url: str, filepath: str) -> bool:
    try:
        with session.get(url, headers=HEADERS, timeout=60, stream=True, allow_redirects=True) as r:
            if r.status_code != 200:
                return False

            content_type = r.headers.get("Content-Type", "").lower()
            content_disposition = r.headers.get("Content-Disposition", "").lower()

            # Accept direct PDFs or download endpoints that serve a PDF/attachment
            if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                if "pdf" not in content_disposition and "attachment" not in content_disposition:
                    return False

            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return True
    except requests.RequestException:
        return False


def main() -> None:
    ensure_dir(OUT_DIR)

    session = requests.Session()

    print("Reading 2025 report index...")
    country_pages = extract_2025_country_pages(session)

    if not country_pages:
        raise RuntimeError("No 2025 country report pages found.")

    print(f"Found {len(country_pages)} country pages:")
    for country, page in sorted(country_pages.items()):
        print(f"  - {country}: {page}")

    rows = []

    for country, page_2025 in sorted(country_pages.items()):
        slug = slugify(country)
        print(f"\n=== {country} ===")

        for year in range(START_YEAR, END_YEAR - 1, -1):
            report_page = make_year_page_url(page_2025, year)
            filename = f"{slug}-report-{year}.pdf"
            outfile = os.path.join(OUT_DIR, filename)

            print(f"Checking {year}: {report_page}")

            pdf_url = find_pdf_download_url(session, report_page)
            if not pdf_url:
                print(f"  Missing: {filename}")
                rows.append({
                    "country": country,
                    "country_slug": slug,
                    "year": year,
                    "filename": filename,
                    "report_page": report_page,
                    "pdf_url": "",
                    "status": "missing"
                })
                continue

            ok = download_file(session, pdf_url, outfile)
            if ok:
                print(f"  Downloaded: {filename}")
                rows.append({
                    "country": country,
                    "country_slug": slug,
                    "year": year,
                    "filename": filename,
                    "report_page": report_page,
                    "pdf_url": pdf_url,
                    "status": "downloaded"
                })
            else:
                print(f"  Download failed: {filename}")
                rows.append({
                    "country": country,
                    "country_slug": slug,
                    "year": year,
                    "filename": filename,
                    "report_page": report_page,
                    "pdf_url": pdf_url,
                    "status": "download_failed"
                })

            time.sleep(1)

    with open(METADATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country",
                "country_slug",
                "year",
                "filename",
                "report_page",
                "pdf_url",
                "status"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Metadata saved to: {METADATA_CSV}")


if __name__ == "__main__":
    main()