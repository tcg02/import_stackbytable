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

# --- SELECTED COLUMNS ONLY ---
column_names = ["NRNA ID", "First Name", "Last Name", "Email", "Phone", "State", "US State"]

records = []
for row in raw_data:
    fields = row.get("field", {})
    if fields.get("Position", "") and str(fields.get("Position", "")).strip().lower() == "state":
        filtered = {key: fields.get(key, None) for key in column_names}
        records.append(filtered)

df = pd.DataFrame(records)

# --- FORMAT NAMES AND CLEAN ---
df["First Name"] = df["First Name"].astype(str).str.title()
df["Last Name"] = df["Last Name"].astype(str).str.title()
df = df[~df["First Name"].str.contains("test", case=False, na=False)]
df = df[~df["Last Name"].str.contains("test", case=False, na=False)]

# Add Position from "State" column
df["Position"] = df["State"]

# --- ROLE ORDER ---
priority_order = [
    "State Chapter President",
    "Chapter Vice President",
    "Chapter Vice President (women)",
    "Chapter Secretary",
    "Chapter Women Secretary",
    "Chapter Treasurer",
    "Chapter Women Coordinator",
    "Chapter Youth Coordinator",
    "chapter board members"
]

def role_priority(val):
    try:
        return priority_order.index(val)
    except ValueError:
        return len(priority_order)

df["role_priority"] = df["Position"].apply(role_priority)
df = df.sort_values(by=["US State", "role_priority", "First Name", "Last Name"])

# --- PDF EXPORT ---
export_columns = ["Position", "NRNA ID", "First Name", "Last Name", "Email", "Phone"]
column_widths = [45, 35, 30, 30, 60, 30]

class PDF(FPDF):
    def header(self):
        pass  # We'll handle title headers manually

    def add_state_title(self, state_name):
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, state_name, ln=True)
        self.ln(1)

    def table_header(self):
        self.set_font("Arial", 'B', 8)
        for col, width in zip(export_columns, column_widths):
            self.cell(width, 6, col, border=1)
        self.ln()

    def row(self, row_data):
        self.set_font("Arial", '', 7)
        for item, width in zip(row_data, column_widths):
            text = str(item) if item else ""
            self.cell(width, 6, text[:40], border=1)
        self.ln()

pdf = PDF(orientation='P', unit='mm', format='A4')
pdf.set_auto_page_break(auto=True, margin=10)
pdf.add_page()

for state, group in df.groupby("US State"):
    pdf.add_state_title(state)
    pdf.table_header()
    for _, row in group[export_columns].iterrows():
        pdf.row(row)
    pdf.ln(5)  # Space between states

pdf.output("state_candidates.pdf")
print("✅ Exported to PDF: state_candidates.pdf")
