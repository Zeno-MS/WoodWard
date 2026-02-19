import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Connect to DB
DB_PATH = "data/woodward.db"
OUTPUT_DIR = "documents/visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def analyze_vendor_spending():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    
    # Query: Aggregated spending by Vendor by Fiscal Year (approximate from dates)
    # We will just group by School Year (e.g. Sep 2023 - Aug 2024 = 2023-24)
    query = """
    SELECT 
        payee,
        entry_date,
        amount
    FROM payments
    WHERE amount > 0
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df)} payment records.")
    
    # Convert date
    df['entry_date'] = pd.to_datetime(df['entry_date'], errors='coerce')
    df = df.dropna(subset=['entry_date'])
    
    # Determine Fiscal Year (July 1 - June 30? Or Sep 1 - Aug 31? WA Schools usually Sep 1)
    # Let's use standard WA Fiscal Year: Sep 1 to Aug 31
    def get_fiscal_year(date):
        if date.month >= 9:
            return f"{date.year}-{str(date.year+1)[2:]}"
        else:
            return f"{date.year-1}-{str(date.year)[2:]}"
    
    df['Fiscal_Year'] = df['entry_date'].apply(get_fiscal_year)
    
    # Standardization mappings (Simple for now, can be expanded)
    cleanup = {
        "SOLIANT": "Soliant",
        "MAXIM": "Maxim",
        "AMERGIS": "Amergis",
        "PIONEER": "Pioneer"
    }
    
    def clean_payee(name):
        name = name.upper()
        for key, val in cleanup.items():
            if key in name:
                return val
        return name
        
    df['Vendor'] = df['payee'].apply(clean_payee)
    
    # Filter for our key vendors
    key_vendors = ["Soliant", "Maxim", "Amergis", "Pioneer"]
    df_key = df[df['Vendor'].isin(key_vendors)]
    
    # 1. Total Spending per Vendor per Year
    annual_spend = df_key.groupby(['Fiscal_Year', 'Vendor'])['amount'].sum().unstack(fill_value=0)
    
    print("\n--- Annual Spending Summary ---")
    print(annual_spend)
    annual_spend.to_csv(f"{OUTPUT_DIR}/vendor_spending_annual.csv")
    
    # Chart 1: Stacked Bar
    plt.figure(figsize=(12, 6))
    annual_spend.plot(kind='bar', stacked=True, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    plt.title('Vendor Spending Trend (2018-2026)')
    plt.ylabel('Total Payments ($)')
    plt.xlabel('Fiscal Year')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/vendor_spending_trend.png")
    print(f"Saved chart to {OUTPUT_DIR}/vendor_spending_trend.png")
    
    # Chart 2: Amergis/Maxim Specific Trend (The 'Rebrand' Tracking)
    # Combine Maxim and Amergis
    df_key['Brand_Group'] = df_key['Vendor'].replace({'Maxim': 'Maxim/Amergis', 'Amergis': 'Maxim/Amergis'})
    maxim_spend = df_key[df_key['Brand_Group'] == 'Maxim/Amergis'].groupby(['Fiscal_Year', 'Vendor'])['amount'].sum().unstack(fill_value=0)
    
    plt.figure(figsize=(10, 6))
    maxim_spend.plot(kind='bar', stacked=True, color=['#ff7f0e', '#d62728']) # Orange for Maxim, Red for Amergis
    plt.title('The Maxim-to-Amergis Transition Spending')
    plt.ylabel('Total Payments ($)')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/maxim_amergis_transition.png")
    print(f"Saved chart to {OUTPUT_DIR}/maxim_amergis_transition.png")

if __name__ == "__main__":
    analyze_vendor_spending()
