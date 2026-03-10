import re

def extract_from_body(text: str) -> dict:

    def find(patterns, default=""):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1)
                if val is not None:
                    return val.strip()
        return default

    vendor = find([
        r"vendor\s*name[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"from[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"best\s*regards[,:\s]*\n([A-Za-z ]+)",
    ])

    invoice_no = find([
        r"invoice\s*(?:no|number|#)[.:\s]*([A-Z0-9\-/]{3,20})",
        r"inv[.\s]*#?\s*([A-Z0-9\-/]{3,20})",
    ])

    invoice_date = find([
        r"invoice\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})",
        r"invoice\s*date[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})"
    ])

    amount_str = find([
        r"total\s*amount[:\s]*\$?([\d,]+\.?\d{0,2})",
        r"(?:grand\s*total|amount\s*due|total\s*due|total)[:\s]*\$?([\d,]+\.?\d{0,2})",
        r"\$\s*([\d,]+\.\d{2})",
    ])

    client_name = find([
        r"client\s*name[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"bill\s*to[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
    ])

    gst_number = find([
        r"gst\s*(?:no|number)?[:\s]+([0-9A-Z]{15})"
    ])

    due_date = find([
        r"due\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})",
        r"due\s*date[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})"
    ])

    due_amount_str = find([
        r"due\s*amount[:\s]*₹?([\d,]+\.?\d{0,2})",
        r"amount\s*due[:\s]*₹?([\d,]+\.?\d{0,2})"
    ])

    total_str = find([
        r"total\s*amount[:\s]*₹?([\d,]+\.?\d{0,2})",
        r"grand\s*total[:\s]*₹?([\d,]+\.?\d{0,2})",
    ])

    try:
        due_amount = float(due_amount_str.replace(",", "")) if due_amount_str else None
    except:
        due_amount = None
    
    try:
        total = float(total_str.replace(",", "")) if total_str else None
    except:
        total = None

    currency = "USD"
    if re.search(r"\b€|EUR\b", text):
        currency = "EUR"
    elif re.search(r"\b£|GBP\b", text):
        currency = "GBP"
    elif re.search(r"₹|INR", text):
        currency = "INR"
    
    text = text.lower()

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