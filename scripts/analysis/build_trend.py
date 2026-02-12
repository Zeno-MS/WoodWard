import pandas as pd
import os

# Setup paths
SALARY_MASTER = "data/salaries/VPS_Top_Salaries_5yr.csv"
STAFFING_DIR = "data/ospi/historical"
CURRENT_STAFFING = "data/ospi/Staffing_Benchmark_2324.csv"

def build_5yr_trend():
    # 1. Salary Trend (Superintendent & Top 10 Average)
    if os.path.exists(SALARY_MASTER):
        sal_df = pd.read_csv(SALARY_MASTER)
        # Sort years: 1920, 2021, 2122, 2223, 2324
        sal_df['Year'] = sal_df['Year'].astype(str)
        
        # Get Superintendent salary per year
        super_sal = sal_df[sal_df['Position'] == 'Superintendent'].groupby('Year')['tfinsal'].max()
        
        # Get Average of Top 10 per year
        top_10_avg = sal_df.groupby('Year').apply(lambda x: x.sort_values('tfinsal', ascending=False).head(10)['tfinsal'].mean())
        
        print("\n--- Salary Trend (Vancouver) ---")
        salary_trend = pd.DataFrame({
            "Superintendent": super_sal,
            "Top 10 Average": top_10_avg
        })
        print(salary_trend)
        salary_trend.to_csv("data/salaries/VPS_Salary_Trend_5yr.csv")

    # 2. Staffing Trend (Principals, Teachers, Paras)
    # We need to parse each year's downloaded tables
    staffing_years = ["2324", "2223", "2122", "2021", "1920"]
    vps_staffing = []

    # Mapping of files
    for year in staffing_years:
        year_data = {"Year": year}
        
        # Current year (2324) from the consolidated benchmark
        if year == "2324" and os.path.exists(CURRENT_STAFFING):
            c_df = pd.read_csv(CURRENT_STAFFING)
            vps_row = c_df[c_df['District'] == 'Vancouver']
            if not vps_row.empty:
                for cat in ["Principals", "Teachers", "Paraeducators"]:
                    if cat in vps_row.columns:
                        year_data[cat] = vps_row[cat].values[0]
        else:
            # Historical years from individual tables
            for cat_id, cat_name in [("17", "Principals"), ("19", "Teachers"), ("20", "Paraeducators")]:
                f_path = os.path.join(STAFFING_DIR, year, f"Table_{cat_id}_{year}.xlsx")
                if os.path.exists(f_path):
                    try:
                        # Find Vancouver (06037)
                        df = pd.read_excel(f_path)
                        # Find header (contains "District")
                        header_row = 0
                        for i, row in df.iterrows():
                             if row.astype(str).str.contains("District", case=False).any():
                                 header_row = i
                                 break
                        df = pd.read_excel(f_path, skiprows=header_row+1)
                        dist_col = df.columns[0]
                        fte_col = None
                        for col in df.columns:
                            if "total" in str(col).lower() and "fte" in str(col).lower():
                                fte_col = col
                                break
                        if not fte_col:
                            for col in df.columns:
                                if "fte" in str(col).lower():
                                    fte_col = col
                                    break
                        
                        match = df[df[dist_col].astype(str).str.contains("06037", na=False)]
                        if not match.empty:
                            year_data[cat_name] = pd.to_numeric(match[fte_col].values[0], errors='coerce')
                    except Exception as e:
                        print(f"Error parsing {f_path}: {e}")
        
        vps_staffing.append(year_data)

    trend_df = pd.DataFrame(vps_staffing).sort_values("Year")
    print("\n--- Staffing Trend (Vancouver FTE) ---")
    print(trend_df)
    trend_df.to_csv("data/ospi/VPS_Staffing_Trend_5yr.csv", index=False)

if __name__ == "__main__":
    build_5yr_trend()
