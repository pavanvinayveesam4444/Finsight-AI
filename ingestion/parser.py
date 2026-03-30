from bs4 import BeautifulSoup
import os
import re

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Common SEC 10-K section header patterns
SEC_SECTION_PATTERNS = re.compile(
    r'(ITEM\s+\d+[A-Z]?\.?\s+|'
    r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+|'
    r'NOTES?\s+TO\s+(CONSOLIDATED\s+)?FINANCIAL\s+|'
    r'MANAGEMENT[\'S]*\s+DISCUSSION|'
    r'QUANTITATIVE\s+AND\s+QUALITATIVE|'
    r'RISK\s+FACTORS|'
    r'BUSINESS\s+OVERVIEW|'
    r'SELECTED\s+FINANCIAL\s+DATA)',
    re.IGNORECASE
)


def _find_table_header(table):
    """
    Walk backwards from a table element to find the nearest section heading.
    Returns a clean header string or empty string if none found.
    Walks up to 3 ancestor levels to handle inline XBRL div-heavy layouts.
    """
    # Skip single-word and ticker-code-style tokens (e.g. "aapl-20250927")
    def _is_usable(text):
        text = re.sub(r'\s+', ' ', text).strip()
        if not (10 < len(text) < 200):
            return False
        # Reject bare ticker codes like "aapl-20250927"
        if re.fullmatch(r'[a-z]+-\d{8}', text, re.IGNORECASE):
            return False
        return True

    node = table
    for _ in range(3):  # walk up to 3 ancestor levels
        for sibling in reversed(list(node.previous_siblings)):
            text = sibling.get_text(separator=" ", strip=True) if hasattr(sibling, 'get_text') else str(sibling).strip()
            text = re.sub(r'\s+', ' ', text).strip()
            if _is_usable(text):
                return text
        if node.parent is None:
            break
        node = node.parent
    return ""


def _is_financial_table(text):
    """Return True if the table text looks like it contains financial data."""
    has_dollar = bool(re.search(r'\$\s*[\d,]+', text))
    has_large_number = bool(re.search(r'\b\d{3},\d{3}\b', text))
    return (has_dollar or has_large_number) and len(text) > 100


def _chunk_text(text, chunk_size=600, overlap=80):
    """Split plain text into overlapping word-count chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) < 50:
            break
        chunks.append(" ".join(chunk_words))
    return chunks


def parse_html_filing(file_path: str, ticker: str, year: str, filing_type: str):
    """
    Extract clean text from an SEC filing HTML file.
    - Financial tables are extracted as their own chunks with section headers as labels.
    - Narrative text is chunked with section-boundary awareness.

    Returns a list of dicts with 'text' and 'metadata'.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")

    # Remove non-content tags
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    chunks = []

    # ── Step 1: Extract financial tables as dedicated chunks ──────────────
    for table in soup.find_all("table"):
        table_text = table.get_text(separator=" ", strip=True)
        table_text = re.sub(r'\s+', ' ', table_text).strip()

        if not _is_financial_table(table_text):
            continue

        header = _find_table_header(table)
        chunk_text = f"{header}\n{table_text}" if header else table_text

        chunks.append({
            "text": chunk_text,
            "metadata": {
                "ticker": ticker,
                "year": year,
                "filing_type": filing_type,
                "source": f"{ticker} {filing_type} {year}",
                "section": header[:80] if header else "Financial Table",
                "chunk_index": len(chunks),
                "chunk_type": "table"
            }
        })

        # Remove table from soup so it isn't double-counted in narrative text
        table.decompose()

    # ── Step 2: Chunk remaining narrative text ────────────────────────────
    raw_text = soup.get_text(separator=" ", strip=True)
    clean_text = re.sub(r'\s+', ' ', raw_text).strip()

    # Split on SEC section boundaries to keep sections together
    parts = re.split(SEC_SECTION_PATTERNS, clean_text)

    current_section = "General"
    for part in parts:
        if part is None:
            continue
        part = part.strip()
        if not part:
            continue

        # If this part looks like a section header, update current_section
        if SEC_SECTION_PATTERNS.match(part):
            current_section = part[:80]
            continue

        for chunk_text in _chunk_text(part):
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "ticker": ticker,
                    "year": year,
                    "filing_type": filing_type,
                    "source": f"{ticker} {filing_type} {year}",
                    "section": current_section,
                    "chunk_index": len(chunks),
                    "chunk_type": "narrative"
                }
            })

    print(f"Parsed {ticker} {filing_type} {year}: {len(chunks)} chunks "
          f"({sum(1 for c in chunks if c['metadata']['chunk_type'] == 'table')} tables, "
          f"{sum(1 for c in chunks if c['metadata']['chunk_type'] == 'narrative')} narrative)")
    return chunks


def parse_all_filings_for_ticker(ticker: str, filing_type: str = "10-K"):
    """
    Parse all downloaded filings for a given ticker.
    Walks through all year folders and parses each filing file found.
    """
    base_path = os.path.join(_PROJECT_ROOT, "data", "raw", "sec-edgar-filings", ticker, filing_type)
    all_chunks = []

    if not os.path.exists(base_path):
        print(f"No filings found for {ticker}. Run edgar_fetcher.py first.")
        return []

    for year_folder in os.listdir(base_path):
        year_path = os.path.join(base_path, year_folder)
        if not os.path.isdir(year_path):
            continue

        match = re.search(r'-(\d{2})-', year_folder)
        year = f"20{match.group(1)}" if match else "Unknown"

        html_files = [f for f in os.listdir(year_path)
                      if f.endswith('.htm') or f.endswith('.html') or f.endswith('.txt')]

        if not html_files:
            continue

        main_file = max(html_files,
                        key=lambda f: os.path.getsize(os.path.join(year_path, f)))
        file_path = os.path.join(year_path, main_file)

        chunks = parse_html_filing(file_path, ticker, year, filing_type)
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    chunks = parse_all_filings_for_ticker("AAPL")
    if chunks:
        print(f"\nTotal chunks: {len(chunks)}")
        table_chunks = [c for c in chunks if c['metadata']['chunk_type'] == 'table']
        print(f"\nSample financial table chunk:")
        print(table_chunks[0]['text'][:500] if table_chunks else "No table chunks found")
