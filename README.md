# FinSight AI — Financial Document Analyst
## The Problem It Solves
- Equity research analysts spend 4-6 hours manually reading SEC filings per
company per earnings cycle. FinSight answers multi-document questions in seconds.
- FP&A analysts spend 3-5 hours writing variance commentary at month-end.
FinSight generates a CFO-ready memo from a CSV upload in 10 seconds.
## Key Features
- **SEC Filings Q&A** — ask questions about 10-K filings with inline citations
- **FP&A Variance Narrator** — upload actuals vs budget, get board/exec/detail memo
- **Multi-company comparison** — compare Apple, Microsoft, Amazon across filings
## Tech Stack
| Component | Technology |
|-----------|------------|
| LLM | Anthropic Claude (claude-sonnet-4) |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | ChromaDB |
| RAG Framework | LangChain |
| Data Source | SEC EDGAR API (free) |
| Frontend | Streamlit |
## Why These Technical Choices
- **Claude over GPT-4** — 200K token context window fits entire 10-K filings in one
call
- **Hybrid retrieval** — combines semantic search with BM25 keyword matching for
financial
figures that semantic search misses
- **Metadata filtering** — every chunk tagged with ticker/year/section for cited
answers
## Quick Start
```bash
git clone https://github.com/yourusername/finsight-ai
cd finsight-ai
pip install -r requirements.txt
cp .env.example .env # Add your API keys
python ingest.py # Download and index filings (~20 min first run)
streamlit run app/main.py
```
## Data Sources
- SEC EDGAR (public, free, no API key required)
- Synthetic P&L data for FP&A demo (included in repo)
