import os
import markdown
from fpdf import FPDF

# Paths
base_dir = "/Users/chrisknight/Projects/WoodWard/VPS_Investigation_Evidence/05_Source_Documents"
files = {
    "doj_press_release_2011_maxim": "DOJ_Maxim_Settlement_2011.pdf",
    "columbian_articles": "Columbian_35M_Cuts_2024.pdf",
    "ospi_secc_21_32": "OSPI_SECC_21_32_Decision.pdf",
    "opb_investigatewest_reporting": "OPB_InvestigateWest_Restraints.pdf"
}

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'ARCHIVED PRIMARY SOURCE DOCUMENT', border=False, align='C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

for md_name, pdf_name in files.items():
    md_path = os.path.join(base_dir, md_name + ".md")
    pdf_path = os.path.join(base_dir, pdf_name)
    
    if os.path.exists(md_path):
        with open(md_path, 'r') as f:
            text = f.read()
            
        # Clean up markdown for simple PDF rendering
        text = text.replace('#', '').replace('**', '').replace('*', '').replace('---', '')
        text = text.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"').replace('—', '-')
        
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(0, 8, text)
        pdf.output(pdf_path)
        print(f"Generated {pdf_name}")
        os.remove(md_path)
    else:
        print(f"Missing {md_path}")
