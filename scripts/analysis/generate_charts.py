import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "woodward.db"
OUTPUT_DIR = PROJECT_ROOT / "documents" / "visualizations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_trend_chart():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT fy.year_label, bo.name, bi.amount 
    FROM budget_items bi 
    JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id 
    JOIN budget_objects bo ON bi.object_id = bo.id 
    WHERE bo.name = 'Purchased Services'
    ORDER BY fy.year_label;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No data found for Purchased Services")
        return

    print("Data found:")
    print(df)
    
    # Convert amounts to millions
    df['amount_millions'] = df['amount'] / 1_000_000
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['year_label'], df['amount_millions'], marker='o', linestyle='-', color='#b71c1c', linewidth=2, markersize=8)
    
    plt.title('VPS Purchased Services (Object 7) Expenditure Trend', fontsize=14, fontweight='bold')
    plt.xlabel('Fiscal Year', fontsize=12)
    plt.ylabel('Amount (Millions USD)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add labels
    for i, txt in enumerate(df['amount_millions']):
        label = f"${txt:.1f}M"
        plt.annotate(label, (df['year_label'][i], df['amount_millions'][i]), 
                     textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold')
        
    plt.tight_layout()
    
    output_file = OUTPUT_DIR / "object7_trend.png"
    plt.savefig(output_file, dpi=300)
    print(f"Chart saved to {output_file}")

if __name__ == "__main__":
    generate_trend_chart()
