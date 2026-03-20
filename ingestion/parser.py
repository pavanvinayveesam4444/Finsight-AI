from bs4 import BeautifulSoup
import os
import json
import re


def parse_html_filing(file_path: str, ticker: str, year: str, filing_type: str):
    """
    Extract clean text from an SEC filing HTML file.
    Splits the text into chunks with metadata attached to each chunk.
    
    Args:
        file_path: Path to the HTML filing file
        ticker: Company stock ticker (e.g. 'AAPL')
        year: Fiscal year (e.g. '2023')
        filing_type: Type of filing (e.g. '10-K')
    
    Returns:
        List of dictionaries, each containing 'text' and 'metadata'
    """
    # Read the HTML file
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()
    
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, "lxml")
    
    # Remove script, style, and other non-content tags
    for unwanted in soup(["script", "style", "meta", "link"]):
        unwanted.decompose()
    
    # Extract the plain text
    raw_text = soup.get_text(separator=" ", strip=True)
    
    # Clean up extra whitespace
    import re
    clean_text = re.sub(r'\s+', ' ', raw_text).strip()
    
    # Split into chunks
    # We use 800 words per chunk with 100-word overlap
    # Overlap prevents answers from being cut off at chunk boundaries
    words = clean_text.split()
    chunk_size = 800
    overlap = 100
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) < 50:  # Skip tiny chunks at the end
            break
        
        chunk_text = " ".join(chunk_words)
        
        # Metadata tells the system WHERE this chunk came from
        # This is what enables cited answers
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "ticker": ticker,
                "year": year,
                "filing_type": filing_type,
                "source": f"{ticker} {filing_type} {year}",
                "chunk_index": len(chunks)
            }
        })
    
    print(f"Parsed {ticker} {filing_type} {year}: {len(chunks)} chunks")
    return chunks


def parse_all_filings_for_ticker(ticker: str, filing_type: str = "10-K"):
    """
    Parse all downloaded filings for a given ticker.
    Walks through all year folders and parses each filing file found.
    """
    base_path = f"data/raw/sec-edgar-filings/{ticker}/{filing_type}"
    all_chunks = []
    
    if not os.path.exists(base_path):
        print(f"No filings found for {ticker}. Run edgar_fetcher.py first.")
        return []
    
    # Walk through year folders
    for year_folder in os.listdir(base_path):
        year_path = os.path.join(base_path, year_folder)
        if not os.path.isdir(year_path):
            continue
        
        # Extract the year from folder name (format is usually YYYY-MM-DD)
        match = re.search(r'-(\d{2})-', year_folder)
        year =f"20{match.group(1)}" if match else "Unknown"
        
        # Find the main filing file (largest .htm or .html file)
        html_files = [f for f in os.listdir(year_path)
              if f.endswith('.htm') or f.endswith('.html') or f.endswith('.txt')]
        
        if not html_files:
            continue
        
        # Use the largest file (usually the main filing, not exhibits)
        main_file = max(html_files,
                       key=lambda f: os.path.getsize(os.path.join(year_path, f)))
        file_path = os.path.join(year_path, main_file)
        
        chunks = parse_html_filing(file_path, ticker, year, filing_type)
        all_chunks.extend(chunks)
    
    return all_chunks


if __name__ == "__main__":
    # Test: parse Apple filings and print first chunk
    chunks = parse_all_filings_for_ticker("AAPL")
    if chunks:
        print(f"\nTotal chunks: {len(chunks)}")
        print(f"\nFirst chunk preview:")
        print(chunks[0]['text'][:500])
        print(f"\nMetadata: {chunks[0]['metadata']}")
