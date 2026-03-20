"""
Main ingestion pipeline.
Run this once to download and index filings for all companies.
After running, your vector database will be ready to query.
"""
from ingestion.edgar_fetcher import fetch_filings
from ingestion.parser import parse_all_filings_for_ticker
from rag.vector_store import add_chunks_to_db, get_collection_stats


# Companies to ingest
# Add more tickers here to expand your database
COMPANIES = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "AMZN",   # Amazon
]

FILING_TYPE = "10-K"
NUM_YEARS = 3


def run_ingestion():
    print("Starting FinSight AI data ingestion...")
    print(f"Companies: {COMPANIES}")
    print(f"Filing type: {FILING_TYPE}")
    print(f"Years: {NUM_YEARS}")
    print("=" * 50)
    
    for ticker in COMPANIES:
        print(f"\nProcessing {ticker}...")
        
        # Step 1: Download filings
        print(f"  Step 1: Downloading filings...")
        fetch_filings(ticker, FILING_TYPE, NUM_YEARS)
        
        # Step 2: Parse filings into chunks
        print(f"  Step 2: Parsing filings...")
        chunks = parse_all_filings_for_ticker(ticker, FILING_TYPE)
        
        if not chunks:
            print(f"  WARNING: No chunks found for {ticker}. Skipping.")
            continue
        
        # Step 3: Store in vector database
        print(f"  Step 3: Storing {len(chunks)} chunks in vector database...")
        add_chunks_to_db(chunks)
        
        print(f"  {ticker} complete!")
    
    print("\n" + "=" * 50)
    print("Ingestion complete!")
    get_collection_stats()


if __name__ == "__main__":
    run_ingestion()
