#!/usr/bin/env python3
"""
Task 2: In-House vs. Contractor Cost Comparison
-----------------------------------------------
INSTRUCTIONS FOR VS CODE + COPILOT:
1. Open this file in VS Code
2. Let Copilot autocomplete the TODO sections
3. Run: python3 scripts/analysis/cost_comparison.py

DATA SOURCES:
- data/woodward.db -> payments table (63k rows)
  Columns: payee, entry_date, amount, source_file
- data/salaries/VPS_Top_Salaries_5yr.csv
  Columns: Year, Position, tfinsal (total final salary)
- Maxim 2021 Rate Schedule (hardcoded below from contract Attachment A)

OUTPUT:
- documents/visualizations/cost_comparison.png
- documents/cost_comparison.csv
"""
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

DB_PATH = "data/woodward.db"
SALARY_PATH = "data/salaries/VPS_Top_Salaries_5yr.csv"
OUTPUT_DIR = "documents/visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Maxim 2021 Contract Rates (from Attachment A) ---
CONTRACTOR_RATES = {
    "BCBA":                  {"low": 85.00, "high": 115.00},
    "BCaBA":                 {"low": 90.00, "high": 90.00},
    "Behavior Tech":         {"low": 50.00, "high": 55.00},
    "Counselor":             {"low": 70.00, "high": 70.00},
    "COTA":                  {"low": 60.00, "high": 65.00},
    "LPN/LVN":               {"low": 55.00, "high": 55.00},
    "O&M Specialist":        {"low": 90.00, "high": 90.00},
    "Paraprofessional":      {"low": 37.00, "high": 45.00},
    "PT/OT":                 {"low": 80.00, "high": 90.00},
    "RN":                    {"low": 70.00, "high": 70.00},
    "School Psychologist":   {"low": 90.00, "high": 110.00},
    "SLP":                   {"low": 80.00, "high": 95.00},
    "SLP-CFY":               {"low": 75.00, "high": 80.00},
    "SLPA":                  {"low": 65.00, "high": 65.00},
    "Social Worker":         {"low": 70.00, "high": 70.00},
    "SPED Teacher":          {"low": 70.00, "high": 80.00},
}

# --- WA State Average Salaries (SEA scale, approximate) ---
# Source: OSPI S-275 + benefits estimate (~35% of salary)
INHOUSE_ANNUAL_COST = {
    "BCBA":                  105_000 * 1.35,  # ~$141,750
    "Behavior Tech":          42_000 * 1.35,  # ~$56,700
    "Counselor":              78_000 * 1.35,  # ~$105,300
    "Paraprofessional":       38_000 * 1.35,  # ~$51,300
    "PT/OT":                  82_000 * 1.35,  # ~$110,700
    "RN":                     72_000 * 1.35,  # ~$97,200
    "School Psychologist":    90_000 * 1.35,  # ~$121,500
    "SLP":                    80_000 * 1.35,  # ~$108,000
    "Social Worker":          72_000 * 1.35,  # ~$97,200
    "SPED Teacher":           75_000 * 1.35,  # ~$101,250
}

# Work hours per year for a school employee (~190 days * 7.5 hrs)
ANNUAL_HOURS = 190 * 7.5  # 1,425 hours

def main():
    # TODO: Copilot — compute the annualized contractor cost per role
    # For each role in CONTRACTOR_RATES, calculate:
    #   annual_contractor_cost = midpoint_hourly_rate * ANNUAL_HOURS
    # Then compare to INHOUSE_ANNUAL_COST for the same role
    
    comparison = []
    for role, rates in CONTRACTOR_RATES.items():
        mid_rate = (rates['low'] + rates['high']) / 2
        annual_contractor = mid_rate * ANNUAL_HOURS
        annual_inhouse = INHOUSE_ANNUAL_COST.get(role)
        
        if annual_inhouse:
            premium_pct = ((annual_contractor - annual_inhouse) / annual_inhouse) * 100
            comparison.append({
                "Role": role,
                "Contractor_Hourly_Mid": mid_rate,
                "Contractor_Annual": annual_contractor,
                "InHouse_Annual": annual_inhouse,
                "Premium_Dollars": annual_contractor - annual_inhouse,
                "Premium_Percent": premium_pct
            })
    
    comp_df = pd.DataFrame(comparison).sort_values("Premium_Percent", ascending=False)
    
    print("=== Cost Comparison: Contractor vs In-House ===")
    print(comp_df.to_string(index=False))
    comp_df.to_csv("documents/cost_comparison.csv", index=False)
    
    # TODO: Copilot — create a horizontal bar chart showing premium % by role
    fig, ax = plt.subplots(figsize=(12, 7))
    
    y = range(len(comp_df))
    bars = ax.barh(y, comp_df['Premium_Percent'], 
                   color=['#dc2626' if p > 0 else '#16a34a' for p in comp_df['Premium_Percent']],
                   edgecolor='white', linewidth=0.5)
    
    ax.set_yticks(y)
    ax.set_yticklabels(comp_df['Role'], fontsize=11)
    ax.set_xlabel('Cost Premium vs. In-House Employee (%)', fontsize=12, fontweight='bold')
    ax.set_title('VPS Contractor Cost Premium by Role\n(Based on Maxim 2021 Contract Rates vs. WA Average + Benefits)',
                 fontsize=13, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.grid(axis='x', linestyle='--', alpha=0.3)
    
    # Annotate bars
    for bar, (_, row) in zip(bars, comp_df.iterrows()):
        width = bar.get_width()
        label = f"+{width:.0f}% (${row['Premium_Dollars']:,.0f}/yr)"
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, label,
                va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/cost_comparison.png", dpi=150, bbox_inches='tight')
    print(f"\nSaved chart to {OUTPUT_DIR}/cost_comparison.png")
    
    # TODO: Copilot — calculate total estimated premium across all contractor spending
    conn = sqlite3.connect(DB_PATH)
    total_contractor = pd.read_sql_query("""
        SELECT SUM(amount) as total FROM payments 
        WHERE amount > 0 AND (
            UPPER(payee) LIKE '%AMERGIS%' OR UPPER(payee) LIKE '%MAXIM HEALTH%'
        )
    """, conn).iloc[0]['total']
    conn.close()
    
    avg_premium = comp_df['Premium_Percent'].mean() / 100
    estimated_overpay = total_contractor * avg_premium / (1 + avg_premium)
    
    print(f"\n=== ESTIMATED TOTAL OVERPAYMENT ===")
    print(f"Total Amergis+Maxim payments: ${total_contractor:,.2f}")
    print(f"Average role premium: {avg_premium*100:.1f}%")
    print(f"Estimated premium paid: ${estimated_overpay:,.2f}")


if __name__ == "__main__":
    main()
