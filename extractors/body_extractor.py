import re


def extract_from_body(text: str) -> dict:
    """
    Extract invoice fields from plain-text email body.
    Handles formats like:
      Vendor: TechNova Solutions
      Invoice Number: INV-1024
      Invoice Date: 05-03-2026
      Total Amount: $1,250.00
    """

    def find(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1)
                if val is not None:
                    return val.strip()
        return default

    vendor = find([
        r"vendor[:\s]+([A-Za-z0-9 ,\.&'-]{3,60})",
        r"(?:from|company|billed?\s*by)[:\s]+([A-Za-z0-9 ,\.&'-]{3,60})",
    ])

    invoice_no = find([
        r"invoice\s*(?:no|number|#)[.:\s]*([A-Z0-9\-/]{3,20})",
        r"inv[.\s]*#?\s*([A-Z0-9\-/]{3,20})",
    ])

    invoice_date = find([
        r"invoice\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})",
        r"date[:\s]+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
    ])

    amount_str = find([
        r"total\s*amount[:\s]*\$?([\d,]+\.?\d{0,2})",
        r"(?:grand\s*total|amount\s*due|total\s*due|total)[:\s]*\$?([\d,]+\.?\d{0,2})",
        r"\$\s*([\d,]+\.\d{2})",
    ])

    try:
        total = float(amount_str.replace(",", "")) if amount_str and isinstance(amount_str, str) else None
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
