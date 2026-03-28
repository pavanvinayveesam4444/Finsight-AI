import streamlit as st
import sys
import os

# Add the project root to the Python path
# This allows importing from rag/, analysis/ etc.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="FinSight AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .main-header { font-size: 3rem !important; font-weight: 700 !important; color: #1F2937; text-align: center; }
    .sub-header { font-size: 1rem; color: #6B7280; margin-bottom: 2rem; text-align: center; }
    .answer-box { background: #F9FAFB; border-left: 4px solid #7C3AED;
                  padding: 1rem; border-radius: 0 8px 8px 0; margin-top: 1rem; }
    .metric-card { background: #FFFFFF; border: 1px solid #E5E7EB;
                   border-radius: 8px; padding: 1rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<h1 class="main-header">FinSight AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered financial document analyst — SEC Filings + FP&A Automation</p>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
mode = st.sidebar.radio(
    "Select a mode:",
    [
        "📄 SEC Filings Q&A",
        "📊 FP&A Variance Analysis",
        "ℹ️ About this project"
    ]
)

# ─────────────────────────────────────────────────────────
# MODE 1: SEC FILINGS Q&A
# ─────────────────────────────────────────────────────────
if mode == "📄 SEC Filings Q&A":
    st.header("Ask Questions About SEC Filings")
    st.markdown("Ask any question about Apple, Microsoft, or Amazon based on their 10-K annual reports.")
    
    # Company selector
    col1, col2 = st.columns([1, 2])
    with col1:
        ticker = st.selectbox(
            "Select company:",
            ["AAPL (Apple)", "MSFT (Microsoft)", "AMZN (Amazon)", "All companies"]
        )
        ticker_code = ticker.split(" ")[0] if "All" not in ticker else None
    
    with col2:
        question = st.text_area(
            "Your question:",
            placeholder="What was Apple's revenue growth in FY2023 and what drove it?",
            height=100
        )
    
    # Example questions
    st.markdown("**Example questions:**")
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    
    example_questions = [
        "What drove Apple's revenue growth in FY2023?",
        "What are Microsoft's main risk factors?",
        "How did Amazon describe its AWS growth strategy?",
    ]
    
    if ex_col1.button(example_questions[0], use_container_width=True):
        question = example_questions[0]
        ticker_code = "AAPL"
    if ex_col2.button(example_questions[1], use_container_width=True):
        question = example_questions[1]
        ticker_code = "MSFT"
    if ex_col3.button(example_questions[2], use_container_width=True):
        question = example_questions[2]
        ticker_code = "AMZN"
    
    # Answer button
    if st.button("Get answer with citations", type="primary"):
        if not question or question.strip() == "":
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Searching filings and generating cited answer..."):
                try:
                    from rag.pipeline import ask
                    answer = ask(question, ticker=ticker_code)
                    
                    st.markdown("### Answer")
                    st.markdown(f'<div class="answer-box">{answer}</div>',
                               unsafe_allow_html=True)
                    
                    st.caption(f"Sources: {ticker_code or 'All companies'} 10-K filings (SEC EDGAR)")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.info("Make sure you have run ingest.py to populate the database first.")

# ─────────────────────────────────────────────────────────
# MODE 2: FP&A VARIANCE ANALYSIS
# ─────────────────────────────────────────────────────────
elif mode == "📊 FP&A Variance Analysis":
    st.header("FP&A Variance Analysis")
    st.markdown("Upload your actuals vs budget P&L and receive CFO-ready commentary in seconds.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload P&L CSV file",
            type=["csv"],
            help="Required columns: line_item, budget_usd, actual_usd"
        )
        st.caption("No data? Download a sample file below.")
        
        with open("data/synthetic/saas_company_pl.csv", "rb") as f:
            st.download_button(
                "Download sample SaaS P&L",
                data=f,
                file_name="sample_pl.csv",
                mime="text/csv"
            )
    
    with col2:
        audience = st.selectbox(
            "Report audience:",
            ["board", "executive", "detail"],
            format_func=lambda x: {
                "executive": "Executive (3 bullets, max 80 words)",
                "board": "Board (2 paragraphs, ~150 words)",
                "detail": "Detail (full analysis, ~350 words)"
            }[x]
        )
        period = st.text_input("Reporting period:", value="Q3 2024")
        company_name = st.text_input("Company name:", value="Your Company")
        threshold = st.slider(
            "Variance threshold (flag if above this %):",
            min_value=1, max_value=20, value=5, step=1
        )
    
    if uploaded_file and st.button("Generate variance memo", type="primary"):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        with st.spinner("Analyzing variances and generating memo..."):
            try:
                from analysis.memo_generator import generate_variance_memo
                result = generate_variance_memo(
                    tmp_path,
                    audience=audience,
                    period=period,
                    company_name=company_name,
                    threshold_pct=float(threshold)
                )
                
                st.markdown("---")
                
                # Display variance table and memo side by side
                left, right = st.columns([1, 1])
                
                with left:
                    st.markdown("### Flagged variances")
                    display_df = result["flagged_items"][[
                        "line_item", "budget_usd", "actual_usd", "variance_usd", "variance_pct"
                    ]].rename(columns={
                        "line_item": "Line Item",
                        "budget_usd": "Budget ($)",
                        "actual_usd": "Actual ($)",
                        "variance_usd": "Variance ($)",
                        "variance_pct": "Variance (%)"
                    })
                    st.dataframe(display_df, use_container_width=True)
                
                with right:
                    st.markdown(f"### {audience.title()}-level memo")
                    st.markdown(f'<div class="answer-box">{result["memo"]}</div>',
                               unsafe_allow_html=True)
                    st.download_button(
                        "Download memo as text",
                        data=result["memo"],
                        file_name=f"variance_memo_{period.replace(' ', '_')}.txt"
                    )
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        os.unlink(tmp_path)

# ─────────────────────────────────────────────────────────
# ABOUT PAGE
# ─────────────────────────────────────────────────────────
elif mode == "ℹ️ About this project":
    st.header("About FinSight AI")
    st.markdown("""
    **FinSight AI** is an AI-powered financial document analyst
    
    ### What it does
    - **Mode 1 — SEC Filings Q&A:** Answers questions about public company 10-K filings
      with source citations, using a RAG (Retrieval-Augmented Generation) architecture.
    - **Mode 2 — FP&A Variance Analysis:** Accepts internal P&L data as a CSV upload,
      detects material variances, and generates CFO-ready commentary in three audience formats.
    
    ### Tech stack
    - **LLM:** Anthropic Claude (200K context window for full 10-K ingestion)
    - **Embeddings:** OpenAI text-embedding-3-small
    - **Vector database:** ChromaDB
    - **RAG framework:** LangChain
    - **Data:** SEC EDGAR API (free, no auth required)
    - **Frontend:** Streamlit
    """)
