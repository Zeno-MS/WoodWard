import pandas as pd

def analyze_cabinet():
    try:
        df23 = pd.read_csv('data/salaries/Top40_2324.csv')
        df24 = pd.read_csv('data/salaries/Top40_2425.csv')
    except Exception as e:
        print(f"Error loading CSVs: {e}")
        return

    # Clean 23-24
    df23_unique = df23.drop_duplicates(subset=['FullName']).copy()
    df23_unique['FullName'] = df23_unique['FullName'].str.strip().str.upper()

    # Clean 24-25 (columns: LastName, FirstName)
    df24['FullName'] = df24['FirstName'].str.strip().str.upper() + " " + df24['LastName'].str.strip().str.upper()
    df24_unique = df24.drop_duplicates(subset=['FullName']).copy()

    left = set(df23_unique['FullName']) - set(df24_unique['FullName'])
    joined = set(df24_unique['FullName']) - set(df23_unique['FullName'])

    print("=== DEPARTED / DEMOTED FROM TOP 40 (2023-24 to 2024-25) ===")
    for name in left:
        sal = df23_unique[df23_unique['FullName'] == name]['tfinsal'].values[0]
        droot = df23_unique[df23_unique['FullName'] == name]['droot'].values[0]
        pos = df23_unique[df23_unique['FullName'] == name].get('Position', pd.Series(['Unknown'])).values[0]
        print(f"{name:30} | Salary 23-24: ${sal:,.0f} | Duty Root: {droot} | Pos: {pos}")

    print("\n=== NEWLY ARRIVED IN TOP 40 (2024-25) ===")
    for name in joined:
        sal = df24_unique[df24_unique['FullName'] == name]['tfinsal'].values[0]
        droot = df24_unique[df24_unique['FullName'] == name]['droot'].values[0]
        print(f"{name:30} | Salary 24-25: ${sal:,.0f} | Duty Root: {droot}")

    print("\n=== ALL DIRECTORS/SUPERVISORS (Duty Root 21) IN 2024-25 ===")
    dirs = df24_unique[df24_unique['droot'] == 21].sort_values(by='tfinsal', ascending=False)
    for _, row in dirs.iterrows():
        print(f"{row['FullName']:30} | Salary: ${row['tfinsal']:,.0f} | Duty Root: {row['droot']}")

if __name__ == "__main__":
    analyze_cabinet()
