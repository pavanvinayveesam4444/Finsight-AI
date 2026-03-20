from rag.vector_store import search_db
from rag.answer_generator import generate_cited_answer


def ask(question: str, ticker: str = None, n_results: int = 6) -> str:
    """
    Main RAG pipeline function.
    Given a question, retrieves relevant filing chunks and returns a cited answer.
    
    Args:
        question: The user's question in plain English
        ticker: Optional company filter (e.g. 'AAPL'). None = search all companies.
        n_results: Number of chunks to retrieve (more = more context, higher cost)
    
    Returns:
        A string containing the answer with inline source citations
    """
    # Step 1: Retrieve relevant chunks
    print(f"Searching database for: '{question}'")
    results = search_db(question, n_results=n_results, ticker=ticker)
    
    num_found = len(results.get('documents', [[]])[0])
    print(f"Found {num_found} relevant chunks")
    
    # Step 2: Generate cited answer
    print("Generating answer...")
    answer = generate_cited_answer(question, results)
    
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
