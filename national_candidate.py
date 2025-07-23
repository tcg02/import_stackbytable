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

# --- ONLY THESE COLUMNS ---
column_names = [
    "NRNA ID", "First Name", "Last Name",
    "Email", "Phone", "National"
]

records = []
for row in raw_data:
    fields = row.get("field", {})
    filtered = {key: fields.get(key, None) for key in column_names}
    records.append(filtered)

df = pd.DataFrame(records)

# ✅ Capitalize first and last names
df["First Name"] = df["First Name"].str.title()
df["Last Name"] = df["Last Name"].str.title()

# ✅ Filter out empty National
df = df[df["National"].notna() & (df["National"].str.strip() != "")]

# ✅ Custom role priority
custom_order = [
    "president",
    "senior vice president",
    "vice president",
    "women vice president",
    "youth vice president",
    "general secretary",
    "secretary (open)",
    "secretary women",
    "treasurer",
    "joint treasurer",
    "youth coordinator",
    "women coordinator",
    "board members woman",
    "board members open",
    "rcc north east",
    "rcc midwest",
    "rcc south",
    "rcc west"
]

# Normalize role variations
normalization_map = {
    "vice-president": "vice president",
    "board of director (open)": "board members open",
    "board of director (woman)": "board members woman"
}

df["__normalized_role__"] = (
    df["National"]
    .str.strip()
    .str.lower()
    .replace(normalization_map)
)

df["__role_rank__"] = df["__normalized_role__"].apply(
    lambda x: custom_order.index(x) if x in custom_order else len(custom_order)
)

# ✅ Sort by role → first name → last name
df = df.sort_values(
    by=["__role_rank__", "First Name", "Last Name"],
    ascending=[True, True, True]
).drop(columns=["__role_rank__", "__normalized_role__"])

print("✅ Filtered and sorted national candidates:")
print(df)

# --- PDF EXPORT CONFIG (fit 6 columns across A4) ---
column_widths = [30, 25, 25, 45, 25, 35]  # Adjusted for readability

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
            self.cell(width, 6, text[:40], border=1)
        self.ln()

# Create and export PDF
pdf = PDF(orientation='P', unit='mm', format='A4')
pdf.set_auto_page_break(auto=True, margin=10)
pdf.add_page()

for _, row in df[column_names].iterrows():
    pdf.row(row)

pdf_filename = "National_Candidates.pdf"
pdf.output(pdf_filename)
print(f"✅ Exported to PDF: {pdf_filename}")
