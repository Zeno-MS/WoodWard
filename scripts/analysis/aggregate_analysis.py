import pandas as pd
import os

VPS_CODE = '06037'

def safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def analyze_aggregates():
    print("Loading datasets...")
    df22 = pd.read_csv('data/salaries/S275_2223.csv', low_memory=False)
    df23 = pd.read_csv('data/salaries/S275_2324.csv', low_memory=False)
    df24 = pd.read_csv('data/salaries/S275_2425_Vancouver_Only.csv', low_memory=False)

    for df in [df22, df23, df24]:
        df.columns = [c.strip() for c in df.columns]
        df['codist'] = df['codist'].astype(str).str.strip().str.replace('"', '')
        
    df22 = df22[df22['codist'].isin([VPS_CODE, '6037', '06037 ', ' 06037'])]
    df23 = df23[df23['codist'].isin([VPS_CODE, '6037', '06037 ', ' 06037'])]
    
    # 1. Deputy Superintendent Vacancy (Duty Root 12)
    print("\n=== DEPUTY SUPERINTENDENT (Duty Root 12) TRACKING ===")
    for year, df in [("2022-23", df22), ("2023-24", df23), ("2024-25", df24)]:
        deputies = df[df['droot'].astype(str).str.strip() == '12']
        if deputies.empty:
            print(f"{year}: VACANT (0 FTE)")
        else:
            names = deputies['LastName'].unique() if 'LastName' in deputies.columns else deputies['FullName'].unique()
            print(f"{year}: {len(names)} Individuals Found - {list(names)}")

    # 2. Total Compensation Pool for Cabinet (Duty Roots 11, 12, 13)
    print("\n=== CABINET COMPENSATION POOL (Duty Roots 11-13) ===")
    roots = ['11', '12', '13']
    for year, df in [("2022-23", df22), ("2023-24", df23), ("2024-25", df24)]:
        cabinet = df[df['droot'].astype(str).str.strip().isin(roots)].copy()
        
        # S-275 reports tfinsal (total final salary) and benefits (cins, cman, cbrtn) per assignment row.
        # We need to drop duplicate person records to get the true total compensation for individuals, 
        # or aggregate tfinsal if taking max per person.
        
        if 'FullName' not in cabinet.columns:
            cabinet['FullName'] = cabinet['LastName'].astype(str) + " " + cabinet['FirstName'].astype(str)
            
        # Group by person to avoid double counting benefits/salary on multiple assignment rows
        person_agg = cabinet.groupby('FullName').agg({
            'tfinsal': 'max',
            'cins': 'max',
            'cman': 'max',
            'cbrtn': 'max',
            'assfte': 'sum'
        })
        
        total_sal = safe_numeric(person_agg['tfinsal']).sum()
        total_ben = (safe_numeric(person_agg['cins']) + safe_numeric(person_agg['cman']) + safe_numeric(person_agg['cbrtn'])).sum()
        total_comp = total_sal + total_ben
        headcount = len(person_agg)
        
        print(f"{year}: {headcount} Headcount | Total Salary: ${total_sal:,.0f} | Total Benefits: ${total_ben:,.0f} | Total Comp: ${total_comp:,.0f}")

    # 3. District-Wide FTE Change (2023-24 vs 2024-25)
    print("\n=== DISTRICT-WIDE FTE CHANGE ===")
    fte23 = safe_numeric(df23['assfte']).sum()
    fte24 = safe_numeric(df24['assfte']).sum()
    print(f"2023-24 District FTE (assfte): {fte23:.2f}")
    print(f"2024-25 District FTE (assfte): {fte24:.2f}")
    print(f"Total FTE Change: {fte24 - fte23:.2f}")

    # 4. Average Salary Weight (Classroom vs Support vs Executive)
    print("\n=== AVERAGE SALARY BY GROUP (2023-24) ===")
    # Define groups based on duty roots
    executive_roots = ['11', '12', '13'] # Superintendent, Deputy, Other District Admin
    classroom_roots = ['31', '32', '33'] # Elem, Secondary, Other Teacher
    support_roots = ['91', '92', '93', '94', '95', '96', '97'] # Various support/classified
    
    if 'FullName' not in df23.columns:
        df23['FullName'] = df23['LastName'].astype(str) + " " + df23['FirstName'].astype(str)

    def print_group_avg(group_name, root_list):
        subset = df23[df23['droot'].astype(str).str.strip().isin(root_list)]
        person_agg = subset.groupby('FullName').agg({'tfinsal': 'max', 'assfte': 'sum'})
        
        full_time = person_agg[person_agg['assfte'] > 0.5]
        avg_sal = safe_numeric(full_time['tfinsal']).mean()
        print(f"{group_name} (Roots {','.join(root_list)}): Avg Salary = ${avg_sal:,.0f} (Based on {len(full_time)} FT individuals)")

    print_group_avg("Executive/Cabinet", executive_roots)
    print_group_avg("Classroom Teachers", classroom_roots)
    print_group_avg("District Support", support_roots)
    
    # 5. Salary-Weighted Impact (Total Payroll Reduction by Tier)
    print("\n=== TOTAL PAYROLL REDUCTION BY TIER (Salary-Weighted Impact) ===")
    def calc_payroll(df, root_list):
        if 'FullName' not in df.columns:
            if 'LastName' in df.columns and 'FirstName' in df.columns:
                df['FullName'] = df['LastName'].astype(str) + " " + df['FirstName'].astype(str)
            else:
                return 0
        subset = df[df['droot'].astype(str).str.strip().isin(root_list)]
        # Use tfinsal maximum per person to avoid double counting multiple assignments
        person_agg = subset.groupby('FullName')['tfinsal'].max()
        return safe_numeric(person_agg).sum()

    for group_name, roots in [("Executive", executive_roots), ("Teachers", classroom_roots), ("Support", support_roots)]:
        pay23 = calc_payroll(df23.copy(), roots)
        pay24 = calc_payroll(df24.copy(), roots)
        reduction = pay23 - pay24
        pct = (reduction / pay23 * 100) if pay23 > 0 else 0
        print(f"{group_name}: 23-24 Payroll = ${pay23:,.0f} | 24-25 Payroll = ${pay24:,.0f} | Reduction = ${reduction:,.0f} ({pct:.1f}%)")

if __name__ == '__main__':
    analyze_aggregates()
