#!/usr/bin/env python3
"""
WoodWard Budget Analysis - Purchased Services Trends
Queries the SQLite database to analyze Object 5 (Purchased Services) spending.
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "woodward.db"

def analyze_purchased_services():
    """Analyze Purchased Services (Object 5) trends."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("WOODWARD BUDGET ANALYSIS: Purchased Services Trends")
    print("=" * 60)
    
    # Get Purchased Services data by year
    cursor.execute("""
        SELECT fy.year_label, bi.amount
        FROM budget_items bi
        JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id
        JOIN budget_objects bo ON bi.object_id = bo.id
        WHERE bo.name = 'Purchased Services'
        ORDER BY fy.year_label
    """)
    
    ps_data = cursor.fetchall()
    
    print("\n📊 Purchased Services by Fiscal Year:")
    print("-" * 40)
    prev_amount = None
    for year, amount in ps_data:
        change = ""
        if prev_amount:
            pct_change = ((amount - prev_amount) / prev_amount) * 100
            change = f"  ({pct_change:+.1f}%)"
        print(f"  {year}: ${amount:,.0f}{change}")
        prev_amount = amount
    
    # Calculate total growth
    if len(ps_data) >= 2:
        first_year, first_amount = ps_data[0]
        last_year, last_amount = ps_data[-1]
        total_growth = ((last_amount - first_amount) / first_amount) * 100
        print(f"\n📈 Total Growth ({first_year} to {last_year}): {total_growth:+.1f}%")
    
    # Compare to total budget
    print("\n📋 Purchased Services as % of Total Budget:")
    print("-" * 40)
    cursor.execute("""
        SELECT fy.year_label, 
               SUM(bi.amount) as total,
               (SELECT bi2.amount FROM budget_items bi2 
                JOIN budget_objects bo2 ON bi2.object_id = bo2.id 
                WHERE bo2.name = 'Purchased Services' 
                AND bi2.fiscal_year_id = fy.id) as ps
        FROM budget_items bi
        JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id
        GROUP BY fy.year_label
        ORDER BY fy.year_label
    """)
    
    for year, total, ps in cursor.fetchall():
        if ps and total:
            pct = (ps / total) * 100
            print(f"  {year}: {pct:.1f}% of total (${ps:,.0f} / ${total:,.0f})")
    
    # Top spending categories comparison
    print("\n🏆 All Categories by Latest Year (2024-2025):")
    print("-" * 40)
    cursor.execute("""
        SELECT bo.name, bi.amount
        FROM budget_items bi
        JOIN fiscal_years fy ON bi.fiscal_year_id = fy.id
        JOIN budget_objects bo ON bi.object_id = bo.id
        WHERE fy.year_label = '2024-2025'
        ORDER BY bi.amount DESC
    """)
    
    for name, amount in cursor.fetchall():
        print(f"  {name}: ${amount:,.0f}")
    
    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    analyze_purchased_services()
