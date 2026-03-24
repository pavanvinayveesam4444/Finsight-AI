import anthropic
from dotenv import load_dotenv
import os
from analysis.variance_engine import load_pl_data, build_variance_summary

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


AUDIENCE_PROMPTS = {
    "executive": """
Write EXACTLY 3 bullet points for a CFO or CEO.
Rules: No jargon. Each bullet is one sentence. Cover only the 3 biggest variances.
Format each bullet as: [Line item]: [What happened] ([$ amount], [% variance])
Total length: 60-80 words maximum.""",
    
    "board": """
Write a 2-paragraph board-level variance commentary.
Paragraph 1 (3-4 sentences): Overall performance summary — revenue, gross margin, EBITDA. Include key drivers.
Paragraph 2 (3-4 sentences): Main cost variances and forward-looking context. End with outlook or management action.
Tone: Formal, measured, professional. Total length: 150-180 words.""",
    
    "detail": """
Write a complete variance analysis memo for the finance team.
Structure:
  1. Executive Summary (2 sentences)
  2. Revenue Analysis (explain each revenue line variance)
  3. Cost Analysis (explain each cost line variance with likely drivers)
  4. Profitability Impact (how variances affected EBITDA and net income)
  5. Recommended Actions (2-3 specific actions finance should take)
Tone: Analytical, specific, actionable. Total length: 300-400 words."""
}


def generate_variance_memo(
    file_path: str,
    audience: str = "board",
    period: str = "Q3 2024",
    company_name: str = "the company",
    threshold_pct: float = 5.0
) -> dict:
    """
    Generate a CFO-ready variance commentary memo.
    
    Args:
        file_path: Path to the P&L CSV file
        audience: 'executive' | 'board' | 'detail'
        period: Reporting period label (e.g. 'Q3 2024')
        company_name: Company name for the memo header
        threshold_pct: Variance threshold for flagging (default 5%)
    
    Returns:
        Dict with 'memo' (the generated text) and 'flagged_items' (the variance table)
    """
    # Load and analyze the data
    df = load_pl_data(file_path)
    variance_summary = build_variance_summary(df, threshold_pct)
    
    # Build the prompt
    prompt = f"""You are an expert FP&A analyst writing monthly variance commentary.
    
Company: {company_name}
Period: {period}
    
VARIANCE DATA:
{variance_summary}
    
WRITING INSTRUCTIONS:
{AUDIENCE_PROMPTS[audience]}
    
Write the variance commentary now:"""
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    
    memo_text = response.content[0].text
    
    from analysis.variance_engine import detect_variances
    flagged = detect_variances(df, threshold_pct)
    
    return {
        "memo": memo_text,
        "flagged_items": flagged,
        "full_data": df,
        "audience": audience,
        "period": period
    }


if __name__ == "__main__":
    # Test all 3 audience formats
    for audience in ["executive", "board", "detail"]:
        print(f"\n{'='*60}")
        print(f"AUDIENCE: {audience.upper()}")
        print("="*60)
        result = generate_variance_memo(
            "data/synthetic/saas_company_pl.csv",
            audience=audience,
            period="Q3 2024",
            company_name="TechCo SaaS"
        )
        print(result["memo"])
