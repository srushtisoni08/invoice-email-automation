import re
import pandas as pd
from pathlib import Path

def extract_from_excel(path: Path) -> dict:
    """Extract invoice fields from an Excel attachment."""
    df = pd.read_excel(path, header=None)
    text = df.to_string()

    def find(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return default

    amount_str = find([r"total[:\s]*([\d,]+\.?\d{0,2})"])
    try:
        total = float(amount_str.replace(",", "")) if amount_str else None
    except ValueError:
        total = None

    return {
        "vendor_name": find([r"vendor[:\s]+(.+)"]),
        "invoice_number": find([r"invoice\s*(?:no|#|number)[:\s]+([A-Z0-9\-/]+)"]),
        "invoice_date": find([r"date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})"]),
        "total_amount": total,
        "currency": "USD",
    }

