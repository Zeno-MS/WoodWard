import os
import shutil
import sqlite3
import pandas as pd
import glob

base_dir = "/Users/chrisknight/Projects/WoodWard"
export_dir = os.path.join(base_dir, "For_NotebookLM")

os.makedirs(export_dir, exist_ok=True)
board_minutes_dir = os.path.join(export_dir, "Board_Minutes")
os.makedirs(board_minutes_dir, exist_ok=True)

# 1. Export DB tables
db_path = os.path.join(base_dir, "data", "woodward.db")
if os.path.exists(db_path):
    print("Exporting database tables...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table_name in tables:
        t_name = table_name[0]
        try:
            df = pd.read_sql_query(f"SELECT * from {t_name}", conn)
            df.to_csv(os.path.join(export_dir, f"db_{t_name}.csv"), index=False)
        except Exception as e:
            print(f"Failed to export {t_name}: {e}")
    conn.close()

# 2. Copy PDFs in documents/F195
print("Copying F-195 PDFs...")
for f in glob.glob(os.path.join(base_dir, "documents", "F195", "*.pdf")):
    shutil.copy(f, export_dir)

# 3. Copy other CSVs
print("Copying CSV data files...")
csv_files = []
csv_files.extend(glob.glob(os.path.join(base_dir, "data", "salaries", "*.csv")))
csv_files.extend(glob.glob(os.path.join(base_dir, "data", "ospi", "*.csv")))
csv_files.extend(glob.glob(os.path.join(base_dir, "documents", "*.csv")))
csv_files.extend(glob.glob(os.path.join(base_dir, "documents", "visualizations", "*.csv")))

for f in csv_files:
    if os.path.exists(f):
        basename = os.path.basename(f)
        dest = os.path.join(export_dir, basename)
        if not os.path.exists(dest):
            shutil.copy(f, dest)

# 4. Copy drafts, briefings, and markdown/txt files
print("Copying drafts and analysis documents...")
md_txt_files = []
md_txt_files.extend(glob.glob(os.path.join(base_dir, "workspaces", "results", "*.md")))
md_txt_files.extend(glob.glob(os.path.join(base_dir, "workspaces", "dispatches", "**", "*.md"), recursive=True))
md_txt_files.extend(glob.glob(os.path.join(base_dir, "workspaces", "dispatches", "**", "*.txt"), recursive=True))
md_txt_files.extend(glob.glob(os.path.join(base_dir, "compass_artifact_*.md")))
md_txt_files.append(os.path.join(base_dir, "VPS_INVESTIGATION_MASTER_PLAN_v2.md"))
md_txt_files.append(os.path.join(base_dir, "investigative_journalist_briefing.md"))
md_txt_files.extend(glob.glob(os.path.join(base_dir, "WoodWard V3", "*.md")))
md_txt_files.append(os.path.join(base_dir, "workspaces", "dispatches", "TO_LEGAL", "03_clause_results.json")) # The contract clauses

for f in md_txt_files:
    if os.path.exists(f):
        basename = os.path.basename(f)
        parent_dir = os.path.basename(os.path.dirname(f))
        
        dest = os.path.join(export_dir, basename)
        if not os.path.exists(dest):
            shutil.copy(f, dest)
        else:
            dest = os.path.join(export_dir, f"{parent_dir}_{basename}")
            shutil.copy(f, dest)

# 5. Copy Board Minutes (PDFs)
print("Copying Board Meeting PDFs...")
board_pdfs = glob.glob(os.path.join(base_dir, "workspaces", "VPS-Board-Scraper", "**", "*.pdf"), recursive=True)
for f in board_pdfs:
    if os.path.exists(f):
        shutil.copy(f, board_minutes_dir)

# 6. Any other stray PDFs at root or documents
for f in glob.glob(os.path.join(base_dir, "*.pdf")):
    shutil.copy(f, export_dir)

print(f"Export complete. Total files in For_NotebookLM: {len(os.listdir(export_dir))} (plus board minutes)")
