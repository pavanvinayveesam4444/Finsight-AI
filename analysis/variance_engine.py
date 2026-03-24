import pandas as pd
from typing import Optional


def load_pl_data(file_path: str) -> pd.DataFrame:
    """
    Load P&L data from a CSV file.
    Calculates variance columns if they are not already present.
    """
    df = pd.read_csv(file_path)
    
    # Standardize column names to lowercase
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    # Ensure required columns exist
    required = ['line_item', 'budget_usd', 'actual_usd']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
    
    # Calculate variance if not present
    if 'variance_usd' not in df.columns:
        df['variance_usd'] = df['actual_usd'] - df['budget_usd']
    if 'variance_pct' not in df.columns:
        df['variance_pct'] = (df['variance_usd'] / df['budget_usd'].abs() * 100).round(1)
    
    return df


def detect_variances(df: pd.DataFrame, threshold_pct: float = 5.0) -> pd.DataFrame:
    """
    Identify all line items where variance exceeds the threshold.
    Returns them sorted by absolute variance magnitude (biggest first).
    """
    flagged = df[df['variance_pct'].abs() >= threshold_pct].copy()
    flagged = flagged.sort_values('variance_pct', key=abs, ascending=False)
    return flagged


def build_variance_summary(df: pd.DataFrame, threshold_pct: float = 5.0) -> str:
    """
    Create a plain-English summary of all material variances.
    This is passed to Claude as context for memo generation.
    """
    flagged = detect_variances(df, threshold_pct)
    
    if flagged.empty:
        return "No material variances detected above the threshold."
    
    total_revenue_row = df[df['line_item'].str.lower().str.contains('total revenue')]
    total_rev_actual = total_revenue_row['actual_usd'].values[0] if len(total_revenue_row) > 0 else None
    total_rev_budget = total_revenue_row['budget_usd'].values[0] if len(total_revenue_row) > 0 else None
    
    lines = []
    
    if total_rev_actual and total_rev_budget:
        rev_var = total_rev_actual - total_rev_budget
        rev_pct = (rev_var / total_rev_budget * 100)
        direction = 'above' if rev_var > 0 else 'below'
        lines.append(f"TOTAL REVENUE: ${total_rev_actual:,.0f} actual vs ${total_rev_budget:,.0f} budget ({rev_pct:.1f}% {direction} budget, ${abs(rev_var):,.0f} variance)")
        lines.append("")
    
    lines.append("MATERIAL VARIANCES (above threshold):")
    for _, row in flagged.iterrows():
        direction = 'favorable' if row['variance_usd'] > 0 else 'unfavorable'
        # For expenses, being below budget is favorable
        if any(word in row['line_item'].lower() for word in
               ['cost', 'expense', 'operating', 'sales', 'marketing', 'g&a', 'r&d']):
            direction = 'favorable' if row['variance_usd'] < 0 else 'unfavorable'
        
        lines.append(
            f"  - {row['line_item']}: ${row['actual_usd']:,.0f} actual vs ${row['budget_usd']:,.0f} budget | "
            f"{abs(row['variance_pct']):.1f}% {direction} | ${abs(row['variance_usd']):,.0f} variance"
        )
    
    return "\n".join(lines)
