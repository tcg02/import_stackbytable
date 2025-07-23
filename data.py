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

# Use the raw response directly
raw_data = response.json()

# --- SELECTED COLUMNS ONLY ---
column_names = [
     "Submitted At", "First Name", "Last Name", "NRNA ID",
    "Email", "Phone", "Position", "National", "US State", "State", "RCC"
]

records = []
for row in raw_data:
    fields = row.get("field", {})
    filtered = {key: fields.get(key, None) for key in column_names}
    records.append(filtered)

df = pd.DataFrame(records)

print("✅ Filtered data loaded successfully")
print(df)

# --- PDF EXPORT ---

# Column widths in mm (total ≤ 270 for A4 landscape)
column_widths = [
    30, 20, 20, 20,   #  Date, First/Last Name, NRNA
    40, 25, 20, 30,   #  Email, Phone, Position, National5
    20, 30, 30            # US State, State, RCC
]

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 7)
        for col, width in zip(column_names, column_widths):
            self.cell(width, 8, col[:20], border=1)
        self.ln()

    def row(self, row_data):
        self.set_font("Arial", '', 6.5)
        for item, width in zip(row_data, column_widths):
            text = str(item) if item else ""
            self.cell(width, 6, text[:35], border=1)
        self.ln()

# Generate the PDF
pdf = PDF(orientation='L', unit='mm', format='A4')
pdf.set_auto_page_break(auto=True, margin=10)
pdf.add_page()

for _, row in df[column_names].iterrows():
    pdf.row(row)

pdf_filename = f"{TABLE_NAME}.pdf"
pdf.output(pdf_filename)
print("✅ Exported to PDF: {pdf_filename}")

# --- OPTIONAL CSV EXPORT ---
# df.to_csv("candidates_filtered.csv", index=False)
# print("✅ Exported to CSV: candidates_filtered.csv")
