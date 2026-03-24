"""
Creates realistic synthetic P&L data for the FP&A demo.
Run this once to generate CSV files in data/synthetic/
"""
import pandas as pd
import os

os.makedirs("data/synthetic", exist_ok=True)

# Scenario 1: SaaS Company
saas_data = {
    "line_item": [
        "Subscription Revenue", "Professional Services", "Total Revenue",
        "Cost of Revenue", "Gross Profit",
        "Sales & Marketing", "Research & Development", "General & Administrative",
        "Total Operating Expenses", "Operating Income (EBIT)",
        "EBITDA", "Net Income"
    ],
    "budget_usd": [
        4500000, 600000, 5100000,
        900000, 4200000,
        1200000, 850000, 450000,
        2500000, 1700000,
        1950000, 1300000
    ],
    "actual_usd": [
        3800000, 400000, 4200000,
        870000, 3330000,
        1380000, 820000, 465000,
        2665000, 665000,
        920000, 490000
    ]
}

df_saas = pd.DataFrame(saas_data)
df_saas["variance_usd"] = df_saas["actual_usd"] - df_saas["budget_usd"]
df_saas["variance_pct"] = (df_saas["variance_usd"] / df_saas["budget_usd"] * 100).round(1)
df_saas.to_csv("data/synthetic/saas_company_pl.csv", index=False)

# Scenario 2: Retail Company
retail_data = {
    "line_item": [
        "Same-Store Sales", "E-commerce Revenue", "Total Revenue",
        "Cost of Goods Sold", "Gross Profit",
        "Store Operations", "Marketing", "Corporate G&A",
        "Total Operating Expenses", "EBIT",
        "EBITDA", "Net Income"
    ],
    "budget_usd": [
        18000000, 4000000, 22000000,
        14300000, 7700000,
        3800000, 1100000, 900000,
        5800000, 1900000,
        2800000, 1200000
    ],
    "actual_usd": [
        17100000, 4800000, 21900000,
        14600000, 7300000,
        3950000, 1250000, 890000,
        6090000, 1210000,
        2220000, 780000
    ]
}

df_retail = pd.DataFrame(retail_data)
df_retail["variance_usd"] = df_retail["actual_usd"] - df_retail["budget_usd"]
df_retail["variance_pct"] = (df_retail["variance_usd"] / df_retail["budget_usd"] * 100).round(1)
df_retail.to_csv("data/synthetic/retail_company_pl.csv", index=False)

print("Demo data created:")
print("  data/synthetic/saas_company_pl.csv")
print("  data/synthetic/retail_company_pl.csv")
