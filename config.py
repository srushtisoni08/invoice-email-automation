import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

ATTACHMENTS_DIR = Path("attachments")
EXCEL_OUTPUT = Path("invoices.xlsx")

ATTACHMENTS_DIR.mkdir(exist_ok=True)