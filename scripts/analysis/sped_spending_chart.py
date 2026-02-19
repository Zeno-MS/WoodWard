#!/usr/bin/env python3
"""
Task 8: SPED Hiring vs. Contractor Spending Visualization
Shows the growth of contractor spending over time alongside 
the decline (or stagnation) of in-house SPED staff.
"""
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

DB_PATH = "data/woodward.db"
OUTPUT_DIR = "documents/visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_fiscal_year(date):
    """WA school fiscal year: Sep 1 - Aug 31"""
    if date.month >= 9:
        return f"{date.year}-{str(date.year+1)[2:]}"
    else:
        return f"{date.year-1}-{str(date.year)[2:]}"


def main():
    conn = sqlite3.connect(DB_PATH)
    
    # ---------------------------------------------------
    # 1. Contractor spending by fiscal year (all SPED vendors)
    # ---------------------------------------------------
    query = """
    SELECT payee, entry_date, amount
    FROM payments
    WHERE amount > 0
    AND (
        UPPER(payee) LIKE '%AMERGIS%'
        OR UPPER(payee) LIKE '%MAXIM HEALTH%'
        OR UPPER(payee) LIKE '%SOLIANT%'
        OR UPPER(payee) LIKE '%PROCARE%'
        OR UPPER(payee) LIKE '%PIONEER HEALTH%'
        OR UPPER(payee) LIKE '%THERAPY%'
        OR UPPER(payee) LIKE '%SUNBELT STAFF%'
        OR UPPER(payee) LIKE '%AVEANNA%'
        OR UPPER(payee) LIKE '%GRAFTON%'
        OR UPPER(payee) LIKE '%LAKEVIEW SPEECH%'
        OR UPPER(payee) LIKE '%HARBOR HEALTH%'
        OR UPPER(payee) LIKE '%ACCOUNTABLE HEALTH%'
        OR UPPER(payee) LIKE '%STUDENT SUCCESS OCC%'
        OR UPPER(payee) LIKE '%SPROUT THERAPY%'
        OR UPPER(payee) LIKE '%STRIDES THERA%'
        OR UPPER(payee) LIKE '%OPEN PATH%'
    )
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['entry_date'] = pd.to_datetime(df['entry_date'], errors='coerce')
    df = df.dropna(subset=['entry_date'])
    df['Fiscal_Year'] = df['entry_date'].apply(get_fiscal_year)
    
    # Vendor grouping
    def categorize_vendor(name):
        name = name.upper()
        if 'AMERGIS' in name or 'MAXIM' in name:
            return 'Amergis/Maxim'
        elif 'PROCARE' in name:
            return 'ProCare Therapy'
        elif 'SOLIANT' in name:
            return 'Soliant Health'
        else:
            return 'Other SPED Vendors'
    
    df['Vendor_Group'] = df['payee'].apply(categorize_vendor)
    
    annual = df.groupby(['Fiscal_Year', 'Vendor_Group'])['amount'].sum().unstack(fill_value=0)
    annual = annual.sort_index()
    
    # Only keep complete-ish fiscal years
    annual = annual[annual.index >= '2020-21']
    
    print("=== SPED Contractor Spending by Fiscal Year ===")
    print(annual)
    print(f"\nTotal: ${annual.sum().sum():,.2f}")
    
    # ---------------------------------------------------
    # 2. Equivalent FTE calculation
    # ---------------------------------------------------
    # Average WA SPED teacher salary: ~$75,000 + ~35% benefits = ~$101,250
    AVG_FTE_COST = 101_250
    annual['Total'] = annual.sum(axis=1)
    annual['Equivalent_FTEs'] = (annual['Total'] / AVG_FTE_COST).round(0).astype(int)
    
    print("\n=== Equivalent In-House FTEs ===")
    for year, row in annual.iterrows():
        print(f"  {year}: ${row['Total']:>14,.2f} = {row['Equivalent_FTEs']:>4} FTEs at ${AVG_FTE_COST:,}")
    
    # ---------------------------------------------------
    # 3. Chart: Stacked bar (vendor groups) + FTE line
    # ---------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Color palette
    colors = {
        'Amergis/Maxim': '#dc2626',      # Red
        'ProCare Therapy': '#f97316',     # Orange
        'Soliant Health': '#eab308',      # Yellow
        'Other SPED Vendors': '#6b7280',  # Gray
    }
    
    # Stacked bars
    plot_cols = [c for c in annual.columns if c not in ['Total', 'Equivalent_FTEs']]
    bar_colors = [colors.get(c, '#94a3b8') for c in plot_cols]
    
    x = range(len(annual))
    bottom = [0] * len(annual)
    
    for col, color in zip(plot_cols, bar_colors):
        values = annual[col].values
        ax1.bar(x, values, bottom=bottom, label=col, color=color, width=0.6, edgecolor='white', linewidth=0.5)
        bottom = [b + v for b, v in zip(bottom, values)]
    
    ax1.set_xlabel('Fiscal Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Contractor Payments ($)', fontsize=12, fontweight='bold', color='#374151')
    ax1.set_xticks(x)
    ax1.set_xticklabels(annual.index, rotation=45, ha='right')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f'${v/1e6:.1f}M'))
    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    
    # FTE line on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(x, annual['Equivalent_FTEs'].values, 'D-', color='#2563eb', linewidth=2.5, 
             markersize=8, markerfacecolor='white', markeredgecolor='#2563eb', markeredgewidth=2,
             label='Equivalent FTEs', zorder=5)
    ax2.set_ylabel('Equivalent Full-Time Employees\n(at $101k avg cost)', fontsize=11, color='#2563eb')
    ax2.tick_params(axis='y', labelcolor='#2563eb')
    
    # Annotate FTEs
    for i, (_, row) in enumerate(annual.iterrows()):
        ax2.annotate(f"{int(row['Equivalent_FTEs'])}", 
                     (i, row['Equivalent_FTEs']), 
                     textcoords="offset points", xytext=(0, 12),
                     ha='center', fontsize=10, fontweight='bold', color='#2563eb')
    
    # Title and legend
    ax1.set_title('Vancouver Public Schools: SPED Contractor Spending\nvs. Equivalent In-House Employees', 
                  fontsize=14, fontweight='bold', pad=15)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9, fontsize=9)
    
    # Add callout box
    latest = annual.iloc[-2] if len(annual) > 1 else annual.iloc[-1]  # Use most recent complete year
    latest_yr = annual.index[-2] if len(annual) > 1 else annual.index[-1]
    callout = f"In {latest_yr}:\n${latest['Total']:,.0f} to contractors\n≈ {int(latest['Equivalent_FTEs'])} teachers' worth"
    ax1.text(0.98, 0.55, callout, transform=ax1.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#fef2f2', edgecolor='#dc2626', alpha=0.9))
    
    plt.tight_layout()
    
    chart_path = f"{OUTPUT_DIR}/sped_hiring_vs_spending.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved chart to {chart_path}")
    
    # ---------------------------------------------------
    # 4. Save data
    # ---------------------------------------------------
    annual.to_csv(f"{OUTPUT_DIR}/sped_contractor_annual.csv")
    print(f"Saved data to {OUTPUT_DIR}/sped_contractor_annual.csv")


if __name__ == "__main__":
    main()
