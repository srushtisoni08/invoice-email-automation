import re
import pdfplumber
from pathlib import Path

def extract_from_pdf(path: Path) -> dict:
    """Extract invoice fields from a PDF using pdfplumber + regex."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    def find(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
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
        r"(?:invoice\s*date|date)[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    ])

    # FIX: added next-line capture for when name is on the line after label
    client_name = find([
        r"(?:bill\s*to|billed\s*to|client|customer)[:\s]+([A-Za-z0-9 ,.&'-]{3,80})",
        r"(?:bill\s*to|billed\s*to|client|customer)[:\s]*\n([A-Za-z0-9 ,.&'-]{3,80})",
    ])

    due_date = find([
        r"(?:due\s*date|payment\s*due)[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"(?:due\s*date)[:\s]+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
        r"(?:due\s*date)[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    ])

    # FIX: support Rs., INR and no-symbol; optional space after symbol
    due_amount_str = find([
        r"(?:amount\s*due|balance\s*due|due\s*amount)[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
    ])

    # FIX: strict 15-char alphanumeric + structural GSTIN fallback
    gst_number = find([
        r"(?:GSTIN|GST\s*No\.?|GST\s*Number)[:\s]*([0-9A-Za-z]{15})",
        r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b",
    ])

    # FIX: specific labels ordered before bare-symbol fallback; support Rs./INR
    amount_str = find([
        r"(?:grand\s*total|total\s*amount|amount\s*payable)[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"(?:amount\s*due|net\s*amount|total)[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"[₹$]\s*([\d,]+\.\d{2})",
    ])

    try:
        total = float(amount_str.replace(",", "")) if amount_str else None
    except ValueError:
        total = None

    try:
        due_amount = float(due_amount_str.replace(",", "")) if due_amount_str else None
    except ValueError:
        due_amount = None

    currency = "INR"
    if re.search(r"₹|INR|Rs\.", text):
        currency = "INR"
    elif re.search(r"\$|USD", text):
        currency = "USD"
    elif re.search(r"€|EUR", text):
        currency = "EUR"
    elif re.search(r"£|GBP", text):
        currency = "GBP"

    return {
        "vendor_name": vendor,
        "client_name": client_name,
        "invoice_number": invoice_no,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "gst_number": gst_number,
        "total_amount": total,
        "due_amount": due_amount,
        "currency": currency,
    }