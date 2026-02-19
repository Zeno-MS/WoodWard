import sqlite3
import pandas as pd

conn = sqlite3.connect('data/woodward.db')

query = """
SELECT 
    payee,
    strftime('%Y', entry_date) as year,
    COUNT(*) as num_payments,
    SUM(amount) as total,
    MIN(entry_date) as first_payment,
    MAX(entry_date) as last_payment
FROM payments
WHERE amount > 0
AND (
    UPPER(payee) LIKE '%AMERGIS%'
    OR UPPER(payee) LIKE '%MAXIM%'
    OR UPPER(payee) LIKE '%SOLIANT%'
    OR UPPER(payee) LIKE '%PROCARE%'
    OR UPPER(payee) LIKE '%PIONEER HEALTH%'
    OR UPPER(payee) LIKE '%THERAPY%'
    OR UPPER(payee) LIKE '%SUNBELT%'
    OR UPPER(payee) LIKE '%AVEANNA%'
    OR UPPER(payee) LIKE '%ACCOUNTABLE HEALTH%'
    OR UPPER(payee) LIKE '%STRIDES%'
    OR UPPER(payee) LIKE '%SPROUT%'
    OR UPPER(payee) LIKE '%STUDENT SUCCESS OCC%'
    OR UPPER(payee) LIKE '%HARBOR HEALTH%'
    OR UPPER(payee) LIKE '%GRAFTON%'
)
GROUP BY payee, year
ORDER BY payee, year
"""

df = pd.read_sql_query(query, conn)
pd.set_option('display.float_format', '${:,.2f}'.format)
pd.set_option('display.max_rows', 200)
pd.set_option('display.width', 160)

print('=== SPED/THERAPY/STAFFING VENDOR SPENDING BY YEAR ===')
print(df.to_string(index=False))

print('\n=== GRAND TOTALS BY VENDOR (All Years) ===')
totals = df.groupby('payee')['total'].sum().sort_values(ascending=False)
for vendor, total in totals.items():
    print(f'  {vendor}: ${total:,.2f}')

print(f'\n=== COMBINED TOTAL ===')
print(f'  ${totals.sum():,.2f}')

conn.close()
