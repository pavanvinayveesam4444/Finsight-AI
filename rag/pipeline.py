from rag.vector_store import search_db
from rag.answer_generator import generate_cited_answer
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()
_claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ALL_TICKERS = ["AAPL", "MSFT", "AMZN"]
TICKER_NAMES = {"AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon"}

# Maps short-form year references to full years stored in metadata
_YEAR_ALIASES = {
    "fy25": "2025", "fy 25": "2025", "2025": "2025", "fiscal 2025": "2025",
    "fy24": "2024", "fy 24": "2024", "2024": "2024", "fiscal 2024": "2024",
    "fy23": "2023", "fy 23": "2023", "2023": "2023", "fiscal 2023": "2023",
    "fy26": "2026", "fy 26": "2026", "2026": "2026", "fiscal 2026": "2026",
}


def _detect_year(question: str) -> str | None:
    """Return the 4-digit year string if the question mentions a specific fiscal year."""
    q = question.lower()
    for alias, year in _YEAR_ALIASES.items():
        if alias in q:
            return year
    return None


def _rewrite_query(question: str) -> str:
    """
    Rewrite the user's question into a search query that will better match
    financial statement text in the vector database.
    """
    msg = _claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": (
                "Rewrite the following question as a dense search query optimized for "
                "retrieving financial statement data from SEC 10-K filings. "
                "Use financial terminology (e.g. 'net sales', 'total revenue', "
                "'consolidated statements of operations', 'fiscal year ended'). "
                "Return only the rewritten query, no explanation.\n\n"
                f"Question: {question}"
            )
        }]
    )
    return msg.content[0].text.strip()


def ask(question: str, ticker: str = None, n_results: int = 25) -> str:
    """
    Main RAG pipeline function.
    Given a question, retrieves relevant filing chunks and returns a cited answer.

    Args:
        question: The user's question in plain English
        ticker: Optional company filter (e.g. 'AAPL'). None = search all companies.
        n_results: Number of chunks to retrieve per company

    Returns:
        A string containing the answer with inline source citations
    """
    print(f"Searching database for: '{question}'")

    search_query = _rewrite_query(question)
    print(f"Rewritten search query: '{search_query}'")

    if ticker is None:
        # Search each company separately, then interleave top-5 per company
        # so every company is represented after the final trim to 15.
        per_company = []
        for t in ALL_TICKERS:
            company_query = f"{TICKER_NAMES[t]}: {search_query}"
            r = search_db(company_query, n_results=n_results, ticker=t)
            per_company.append((
                r.get("documents", [[]])[0],
                r.get("metadatas", [[]])[0],
                r.get("distances", [[]])[0],
            ))

        # Round-robin interleave: take 1 chunk from each company in turn
        interleaved_docs, interleaved_metas, interleaved_dists = [], [], []
        max_len = max(len(p[0]) for p in per_company)
        for i in range(max_len):
            for docs, metas, dists in per_company:
                if i < len(docs):
                    interleaved_docs.append(docs[i])
                    interleaved_metas.append(metas[i])
                    interleaved_dists.append(dists[i])

        results = {
            "documents": [interleaved_docs],
            "metadatas": [interleaved_metas],
            "distances": [interleaved_dists],
        }
    else:
        results = search_db(search_query, n_results=n_results, ticker=ticker)

    num_found = len(results.get('documents', [[]])[0])
    print(f"Found {num_found} relevant chunks")

    # If the question targets a specific year, promote year-filtered table chunks
    # to the front so they aren't crowded out by better-labelled older chunks.
    target_year = _detect_year(question)
    if target_year:
        tickers_to_search = [ticker] if ticker else ALL_TICKERS
        pinned_docs, pinned_metas, pinned_dists = [], [], []
        for t in tickers_to_search:
            yr = search_db(search_query, n_results=10, ticker=t, year=target_year)
            for doc, meta, dist in zip(
                yr.get("documents", [[]])[0],
                yr.get("metadatas", [[]])[0],
                yr.get("distances", [[]])[0],
            ):
                if meta.get("chunk_type") == "table" and doc not in pinned_docs:
                    pinned_docs.append(doc)
                    pinned_metas.append(meta)
                    pinned_dists.append(dist)

        if pinned_docs:
            # Remove these chunks from wherever they sit in results, then prepend
            pinned_set = set(pinned_docs)
            remaining = [
                (d, m, s)
                for d, m, s in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
                if d not in pinned_set
            ]
            rem_docs, rem_metas, rem_dists = zip(*remaining) if remaining else ([], [], [])
            results["documents"][0] = pinned_docs + list(rem_docs)
            results["metadatas"][0] = pinned_metas + list(rem_metas)
            results["distances"][0] = pinned_dists + list(rem_dists)

    # Trim to top 15 chunks for generation to stay within token limits
    MAX_CONTEXT_CHUNKS = 15
    docs = results["documents"][0][:MAX_CONTEXT_CHUNKS]
    trimmed = {
        "documents": [docs],
        "metadatas": [results["metadatas"][0][:MAX_CONTEXT_CHUNKS]],
        "distances": [results["distances"][0][:MAX_CONTEXT_CHUNKS]],
    }

    # Step 2: Generate cited answer
    print("Generating answer...")
    answer = generate_cited_answer(question, trimmed)
    
    return answer


if __name__ == "__main__":
    # Test questions
    test_questions = [
        ("What was Apple's total revenue in fiscal year 2023?", "AAPL"),
        ("What are the main risk factors Apple disclosed in its latest 10-K?", "AAPL"),
        ("How did Microsoft describe its cloud computing growth strategy?", "MSFT"),
    ]
    
    for question, ticker in test_questions:
        print("\n" + "="*60)
        print(f"Q: {question}")
        print(f"Company: {ticker}")
        print("-"*60)
        answer = ask(question, ticker=ticker)
        print(answer)
        print("="*60)
