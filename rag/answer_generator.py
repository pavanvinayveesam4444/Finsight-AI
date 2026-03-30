import anthropic
from dotenv import load_dotenv
import os

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_cited_answer(question: str, retrieved_results: dict) -> str:
    """
    Send the user's question + retrieved chunks to Claude.
    Claude reads the chunks and writes an answer with source citations.
    """
    # Extract the retrieved documents and their metadata
    documents = retrieved_results.get("documents", [[]])[0]
    metadatas = retrieved_results.get("metadatas", [[]])[0]
    
    if not documents:
        return "No relevant information found in the database. Try rephrasing your question or check that the company's filings have been ingested."
    
    # Build the context string
    # Each chunk is labeled with a source number so Claude can cite it
    context_parts = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        source_label = f"[Source {i+1}: {meta.get('ticker', 'Unknown')} {meta.get('filing_type', '')} {meta.get('year', '')}]"
        context_parts.append(f"{source_label}\n{doc}")
    
    context = "\n\n" + "-"*40 + "\n\n".join(context_parts)
    
    # The prompt tells Claude exactly how to behave:
    # - Only use the provided documents (no hallucination)
    # - Cite every fact with a source number
    # - Be direct and specific like a real financial analyst
    prompt = f"""You are a financial analyst assistant helping with research on US public companies.

INSTRUCTIONS:
1. Answer the question using ONLY the information in the source documents below
2. Every specific fact, number, or claim must be cited with its source number like this: [Source 1] or [Source 2]
3. If a piece of information is from multiple sources, cite all of them: [Source 1][Source 3]
4. If the documents do not contain enough information to answer fully, say so clearly
5. Be specific with numbers - do not round or paraphrase figures unless necessary
6. Write in the style of a professional financial analyst: direct, precise, and data-driven

SOURCE DOCUMENTS:
{context}

QUESTION: {question}

ANALYSIS:"""
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text
