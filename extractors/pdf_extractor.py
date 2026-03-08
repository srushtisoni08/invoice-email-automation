import re
import pdfplumber
from pathlib import Path

def extract_from_pdf(path: Path) -> dict:
    """Extract invoice fields from a PDF using pdfplumber + regex."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"

    def find(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return default

    vendor = find([
        r"(?:vendor|supplier|company|sold\s*by|billed\s*by|from)[:\s]+([A-Za-z0-9 ,.&'-]{3,80})",
        r"^([A-Z][A-Za-z0-9 ,.&'-]{3,80})\n",
    ])

    invoice_no = find([
        r"invoice\s*(?:no|number|#|id)[.:\s]*([A-Z0-9\-/]{3,30})",
        r"inv[.\s]*#?\s*([A-Z0-9\-/]{3,30})",
    ])

    invoice_date = find([
        r"(?:invoice\s*date|date\s*of\s*invoice|date)[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"(?:invoice\s*date|date)[:\s]+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
    ])

    amount_str = find([
    r"(?:grand\s*total|total\s*amount|amount\s*payable|amount\s*due|net\s*amount|total)[:\s₹$]*([\d,]+\.?\d{0,2})",
    r"[₹$]\s*([\d,]+\.\d{2})",
    ])
    try:
        total = float(amount_str.replace(",", "")) if amount_str else None
    except ValueError:
        total = None

    currency = "INR"

    if re.search(r"₹|INR", text):
        currency = "INR"
    elif re.search(r"\$", text):
        currency = "USD"
    elif re.search(r"€|EUR", text):
        currency = "EUR"
    elif re.search(r"£|GBP", text):
        currency = "GBP"

    return {
        "vendor_name": vendor,
        "invoice_number": invoice_no,
        "invoice_date": invoice_date,
        "total_amount": total,
        "currency": currency,
    }
