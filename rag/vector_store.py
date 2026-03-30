import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Absolute path so the app finds the database no matter where it's launched from
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma_client = chromadb.PersistentClient(path=os.path.join(_PROJECT_ROOT, "data", "chroma_db"))


def get_embedding(text: str) -> list:
    """
    Convert text into a vector (list of numbers) using OpenAI embeddings.
    This vector captures the meaning of the text.
    """
    # Truncate to avoid exceeding token limits
    text = text[:8000]
    
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def add_chunks_to_db(chunks: list, collection_name: str = "filings"):
    """
    Add document chunks to the vector database.
    Each chunk gets converted to an embedding and stored with its metadata.
    """
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    
    print(f"Adding {len(chunks)} chunks to database...")
    
    # Process in batches to avoid overwhelming the API
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        
        # Create unique IDs for each chunk
        ids = [
            f"{c['metadata']['ticker']}_{c['metadata']['year']}_{c['metadata']['chunk_index']}"
            for c in batch
        ]
        
        # Get embeddings for all texts in this batch
        embeddings = [get_embedding(text) for text in texts]
        
        # Add to ChromaDB
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"  Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
    
    print(f"Done! {len(chunks)} chunks stored in '{collection_name}' collection.")


def search_db(query: str, n_results: int = 6,
              ticker: str = None, year: str = None,
              collection_name: str = "filings"):
    """
    Search the vector database for chunks relevant to the query.

    Args:
        query: The user's question
        n_results: How many chunks to retrieve
        ticker: Optional - filter to a specific company
        year: Optional - filter to a specific filing year (e.g. '2025')
        collection_name: Which ChromaDB collection to search
    """
    collection = chroma_client.get_or_create_collection(collection_name)
    query_embedding = get_embedding(query)

    # Build filter
    filters = {}
    if ticker:
        filters["ticker"] = ticker
    if year:
        filters["year"] = year
    if len(filters) == 1:
        where = filters
    elif len(filters) > 1:
        where = {"$and": [{k: v} for k, v in filters.items()]}
    else:
        where = None
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    return results


def clear_collection(collection_name: str = "filings"):
    """Delete and recreate the collection to start fresh."""
    try:
        chroma_client.delete_collection(collection_name)
        print(f"Cleared collection '{collection_name}'")
    except Exception:
        print(f"Collection '{collection_name}' did not exist, nothing to clear")


def get_collection_stats(collection_name: str = "filings"):
    """Get the number of chunks stored in a collection."""
    try:
        collection = chroma_client.get_collection(collection_name)
        count = collection.count()
        print(f"Collection '{collection_name}' contains {count} chunks")
        return count
    except Exception:
        print(f"Collection '{collection_name}' does not exist yet")
        return 0


if __name__ == "__main__":
    get_collection_stats()

