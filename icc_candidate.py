import requests
import pandas as pd
from dotenv import load_dotenv
import os
from fpdf import FPDF

# --- LOAD ENV ---
load_dotenv()
API_KEY = os.getenv("STACKBY_API_KEY")
STACK_ID = os.getenv("STACKBY_STACK_ID")
TABLE_NAME = os.getenv("STACKBY_TABLE_NAME")

BASE_URL = "https://stackby.com/api/v1"
URL = f"{BASE_URL}/rowlist/{STACK_ID}/{TABLE_NAME}?latest=true"

HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

# --- FETCH DATA ---
try:
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    exit()

raw_data = response.json()

# --- SELECTED COLUMNS ---
column_names = [
    "NRNA ID", "First Name", "Last Name", "Email", "Phone", "Position"
]

records = []
for row in raw_data:
    fields = row.get("field")
    if not fields:
        continue
    position = fields.get("Position", "")
    if position and position.strip() == "ICC":
        record = {key: fields.get(key, "") for key in column_names}
        record["ICC"] = fields.get("ICC", "")
        records.append(record)

if not records:
    print("⚠️ No ICC entries found.")
    exit()

# Capitalize names for sorting
for r in records:
    r["First Name"] = str(r.get("First Name", "")).strip().title()
    r["Last Name"] = str(r.get("Last Name", "")).strip().title()

# Convert to DataFrame
columns = ["NRNA ID", "First Name", "Last Name", "Email", "Phone"]
df = pd.DataFrame(records)

# --- PDF EXPORT ---
class PDF(FPDF):
    def header(self):
        pass

    def icc_title(self, title):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, title, ln=True)
        self.ln(1)

    def table_header(self):
        self.set_font("Arial", 'B', 9)
        col_widths = [28, 30, 30, 55, 35, 50]
        for col, width in zip(columns, col_widths):
            self.cell(width, 8, col, border=1)
        self.ln()

    def row(self, row_data):
        self.set_font("Arial", '', 8)
        col_widths = [28, 30, 30, 55, 35, 50]
        for val, width in zip(row_data, col_widths):
            text = str(val) if val else ""
            self.cell(width, 6, text[:45], border=1)
        self.ln()

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# --- GROUP AND EXPORT BY ICC ---
for icc_value, group_df in df.groupby("ICC"):
    group_df = group_df.sort_values(by=["First Name", "Last Name"])
    pdf.icc_title(icc_value if icc_value else "Unknown ICC")
    pdf.table_header()
    for _, row in group_df.iterrows():
        pdf.row(row[columns])
    pdf.ln(5)

pdf.output("icc_candidates.pdf")
print("✅ Exported to PDF: icc_candidates.pdf")
