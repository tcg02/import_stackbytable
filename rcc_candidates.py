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
    if position and position.strip() == "Regional Committee Chair (RCC)":
        record = {key: fields.get(key, "") for key in column_names}
        record["RCC"] = fields.get("RCC", "")
        records.append(record)

if not records:
    print("⚠️ No RCC entries found.")
    exit()

# Capitalize names for sorting
for r in records:
    r["First Name"] = str(r.get("First Name", "")).strip().title()
    r["Last Name"] = str(r.get("Last Name", "")).strip().title()

# Convert to DataFrame
columns = ["NRNA ID", "First Name", "Last Name", "Email", "Phone", "Position"]
df = pd.DataFrame(records)

# --- PDF EXPORT ---
class PDF(FPDF):
    def header(self):
        pass

    def rcc_title(self, title):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, title, ln=True)
        self.ln(1)

    def table_header(self):
        self.set_font("Arial", 'B', 9)
        col_widths = [25, 25, 25, 40, 35, 45]  # adjusted widths to fit better
        for col, width in zip(columns, col_widths):
            self.cell(width, 8, col, border=1)
        self.ln()

    def row(self, row_data):
        self.set_font("Arial", '', 8)
        col_widths = [25, 25, 25, 40, 35, 45]  # match header
        for val, width in zip(row_data, col_widths):
            text = str(val) if val else ""
            self.cell(width, 6, text[:40], border=1)
        self.ln()


pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# --- GROUP AND EXPORT BY RCC ---
for rcc_value, group_df in df.groupby("RCC"):
    group_df = group_df.sort_values(by=["First Name", "Last Name"])
    pdf.rcc_title(rcc_value if rcc_value else "Unknown RCC")
    pdf.table_header()
    for _, row in group_df.iterrows():
        pdf.row(row[columns])
    pdf.ln(5)

pdf.output("rcc_candidates.pdf")
print("✅ Exported to PDF: rcc_candidates.pdf")