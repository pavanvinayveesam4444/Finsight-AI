# Copilot Instructions for FinSight

## Project Overview
**FinSight** is a financial document analysis platform using Retrieval-Augmented Generation (RAG) to extract insights from SEC filings and financial documents. The stack combines LLMs (Anthropic Claude, OpenAI), LangChain orchestration, ChromaDB vector storage, and Streamlit UI.

## Architecture & Data Flow

### Core Components
- **`ingestion/`**: SEC EDGAR downloader pipeline (via `sec-edgar-downloader`). Processes PDFs with `pdfplumber` and `beautifulsoup4` for extraction. Output: raw financial documents stored in `data/raw/`.
- **`rag/`**: Retrieval-Augmented Generation logic. Uses LangChain for embedding + retrieval chains combining ChromaDB vector store with Claude/GPT LLMs.
- **`analysis/`**: Financial analysis and metrics computation. Processes extracted data to generate insights and visualizations.
- **`app/`**: Streamlit frontend. User interface for querying documents and viewing analysis results.
- **`data/`**: Data storage hierarchy:
  - `raw/`: Original SEC filings (PDFs)
  - `processed/`: Cleaned/parsed financial data
  - `synthetic/`: Generated/synthetic data for testing
  - `chroma_db/`: Vector database (ChromaDB persisted storage)
- **`prompts/`**: Prompt templates for LLM orchestration
- **`tests/`**: Unit/integration tests

### Key Data Flow
1. **Ingestion**: SEC documents → PDF extraction → Text parsing → `data/raw/`
2. **Processing**: Raw documents → Chunking & cleaning → `data/processed/`
3. **Vectorization**: Documents → Embeddings (via LangChain) → ChromaDB
4. **Querying**: User query → Retrieval (BM25 + vector similarity) → LLM context window → Response
5. **Analysis**: Structured financial data → Metrics computation → Plotly visualizations

## Development Patterns & Conventions

### LLM Integration
- **Model selection**: Claude (`anthropic>=0.25.0`) preferred for analysis; OpenAI available for comparison
- **Environment setup**: `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` required in `.env`
- **LangChain usage**: Always import from `langchain` + specific providers (`langchain-anthropic`, `langchain-openai`)
  ```python
  from langchain_anthropic import ChatAnthropic
  from langchain_openai import ChatOpenAI
  from langchain.chains import RetrievalQA
  ```

### Vector Database
- **ChromaDB persistence**: Stored in `data/chroma_db/`. Initialize with persistent path for cross-session retrieval
- **Embedding strategy**: Use LangChain's embedding wrappers (defaults to OpenAI embeddings)
- **Hybrid search**: Implement BM25 (via `rank-bm25`) + vector similarity for robust document retrieval

### Data Processing
- **PDF extraction**: Use `pdfplumber` for tabular data; `beautifulsoup4` for HTML-parsed content
- **Data export**: `pandas` DataFrames with `openpyxl` for Excel output; `numpy` for numerical operations
- **Visualization**: Plotly for interactive financial charts (time series, distributions, heatmaps)

### Dependencies & External APIs
- **SEC EDGAR**: `sec-edgar-downloader` handles authentication and rate limiting
- **HTTP requests**: Use `requests` library; handle rate limits with exponential backoff
- **API rate limits**: Implement caching for repeated queries; respect ChromaDB batch operations

## Testing & Validation

- **Test structure**: `tests/` directory mirrors source structure (e.g., `tests/test_rag.py` → `rag/` module)
- **Fixtures**: Use real financial documents from `data/synthetic/` for reproducible testing
- **Integration tests**: Verify end-to-end: ingestion → processing → RAG retrieval → response quality

## Common Workflows

### Local Development
```bash
source venv/bin/activate
pip install -r requirements.txt
# Run Streamlit app
streamlit run app/main.py
```

### Adding a New Document Type
1. Add parser in `ingestion/parsers/` (extend `BasePDFParser` if pattern exists)
2. Register in ingestion pipeline
3. Add test case in `tests/test_ingestion.py`
4. Update `prompts/` with document-specific extraction templates

### Debugging LLM Responses
- Enable LangChain debug logging: `langchain.debug = True`
- Check prompt templates in `prompts/` for hallucination indicators
- Validate retrieved context: ensure ChromaDB returns relevant documents before LLM call
- Use synthetic data in `data/synthetic/` to isolate issues

## File Conventions
- Module-level docstrings: Explain purpose and key public functions
- Logging: Use `logging` module (configure in app initialization)
- Configuration: External params via `.env` (never hardcode API keys)
- Error handling: Raise custom exceptions with context (e.g., `IngestionError`, `RetrievalError`)

## Known Limitations & Future Patterns
- ChromaDB in-memory fallback if persistence fails (implement recovery logic)
- LLM context window constraints: Implement sliding window for large documents
- Token counting: Use `tiktoken` to estimate costs before API calls (if budget tracking needed)
