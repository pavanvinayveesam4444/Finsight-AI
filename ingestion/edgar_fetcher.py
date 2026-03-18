from sec_edgar_downloader import Downloader
import os


def fetch_filings(ticker: str, filing_type: str = "10-K", num_filings: int = 3):
    """
    Download SEC filings for a company.
    
    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL' for Apple)
        filing_type: Type of filing ('10-K', '10-Q', '8-K')
        num_filings: How many recent filings to download
    
    Returns:
        Path to the folder where filings were saved
    """
    # Create the download directory if it does not exist
    os.makedirs("data/raw", exist_ok=True)
    
    # Initialize the downloader
    # Replace 'your@email.com' with your real email
    # SEC requires this for rate limiting but does not send emails
    dl = Downloader("FinSightAI", "your@email.com", "data/raw")
    
    print(f"Downloading {num_filings} {filing_type} filings for {ticker}...")
    dl.get(filing_type, ticker, limit=num_filings)
    
    save_path = f"data/raw/{ticker}/{filing_type}"
    print(f"Done. Files saved to: {save_path}")
    return save_path


if __name__ == "__main__":
    # Test: download filings for Apple, Microsoft, and Amazon
    # Start with just Apple to make sure it works
    fetch_filings("AAPL", "10-K", num_filings=3)
    print("Apple filings downloaded successfully!")
