import re
import pandas as pd
from pathlib import Path

def extract_from_excel(path: Path) -> dict:
    """Extract invoice fields from an Excel attachment."""
    df = pd.read_excel(path, header=None)
    text = df.to_string()

    def find(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return default

    # FIX: added all missing fields (client_name, due_date, gst_number, due_amount, currency)
    vendor = find([r"vendor\s*(?:name)?[:\s]+(.+)"])

    invoice_no = find([r"invoice\s*(?:no|#|number)[:\s]+([A-Z0-9\-/]+)"])

    invoice_date = find([
        r"invoice\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"(?<!\w)date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
    ])

    client_name = find([
        r"client\s*(?:name)?[:\s]+([A-Za-z0-9 ,.'&-]{3,80})",
        r"bill(?:ed)?\s*to[:\s]+([A-Za-z0-9 ,.'&-]{3,80})",
    ])

    due_date = find([
        r"due\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"payment\s*due[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
    ])

    gst_number = find([
        r"(?:GSTIN|GST\s*(?:No\.?|Number)?)[:\s]*([0-9A-Za-z]{15})",
        r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b",
    ])

    total_str = find([
        r"total\s*amount[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"grand\s*total[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"total[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
    ])

    due_amount_str = find([
        r"due\s*amount[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"amount\s*due[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
    ])

    try:
        total = float(total_str.replace(",", "")) if total_str else None
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