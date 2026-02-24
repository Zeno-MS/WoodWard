import pandas as pd
import glob
import os

target_names = ["FISH", "BLECHSCHMIDT"]

files = glob.glob("data/salaries/S275_2324.csv")
if not files:
    print("No 2324 file found")
else:
    f = files[0]
    df = pd.read_csv(f, low_memory=False)
    
    # Just search by name without codist filter to see what codist they are in
    if "LastName" in df.columns:
        # handle nan
        targets = df[df["LastName"].fillna("").str.upper().str.contains("FISH|BLECHSCHMIDT", regex=True)]
        if not targets.empty:
            print("Found targets:")
            print(targets[["LastName", "FirstName", "codist", "tfinsal"]].to_string())
        else:
            print("No matching names found anywhere.")
