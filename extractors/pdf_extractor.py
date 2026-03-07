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
        r"(?:from|vendor|billed?\s*by|company)[:\s]+([A-Za-z0-9 ,\.&'-]{3,50})",
        r"^([A-Z][A-Za-z0-9 ,\.&'-]{2,40})\n",
    ])

    invoice_no = find([
        r"invoice\s*(?:no|number|#)[.:\s]*([A-Z0-9\-/]{3,20})",
        r"inv[.\s]*#?\s*([A-Z0-9\-/]{3,20})",
    ])

    invoice_date = find([
        r"(?:invoice\s*date|date\s*of\s*invoice|date)[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"(?:invoice\s*date|date)[:\s]+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
    ])

    amount_str = find([
        r"(?:total\s*amount|grand\s*total|amount\s*due|total\s*due|total)[:\s]*\$?([\d,]+\.?\d{0,2})",
        r"\$\s*([\d,]+\.\d{2})\s*$",
    ])
    try:
        total = float(amount_str.replace(",", "")) if amount_str else None
    except ValueError:
        total = None

    currency = "USD"
    if re.search(r"\b€|EUR\b", text):
        currency = "EUR"
    elif re.search(r"\b£|GBP\b", text):
        currency = "GBP"

    return {
        "vendor_name": vendor,
        "invoice_number": invoice_no,
        "invoice_date": invoice_date,
        "total_amount": total,
        "currency": currency,
    }
