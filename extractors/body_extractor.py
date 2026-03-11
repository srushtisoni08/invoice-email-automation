import re

def extract_from_body(text: str) -> dict:
    clean = re.sub(r"^\s*[\*\-\•]\s*", "", text, flags=re.MULTILINE)

    def find(patterns, default=""):
        for pat in patterns:
            for t in (clean, text):          # try cleaned text first, then raw
                m = re.search(pat, t, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = m.group(1)
                    if val is not None:
                        return val.strip()
        return default

    vendor = find([
        r"vendor\s*name\s*[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",   # "Vendor Name: X"
        r"(?<!\w)vendor\s*[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",   # "Vendor: X"
        r"supplier\s*(?:name)?\s*[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"from\s*[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"best\s*regards[,:\s]*\n([A-Za-z ]+)",
    ])

    invoice_no = find([
        r"invoice\s*(?:no|number|#)[.:\s]*([A-Z0-9\-/]{3,20})",
        r"inv[.\s]*#?\s*([A-Z0-9\-/]{3,20})",
    ])

    invoice_date = find([
        r"invoice\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})",
        r"invoice\s*date[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        r"invoice\s*date[:\s]+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
    ])

    client_name = find([
        r"client\s*(?:name)?\s*[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"bill(?:ed)?\s*to\s*[:\s]+([A-Za-z0-9 ,.'&-]{3,60})",
        r"bill(?:ed)?\s*to\s*[:\s]*\n([A-Za-z0-9 ,.'&-]{3,60})",
    ])

    gst_number = find([
        r"(?:GSTIN|GST\s*(?:No\.?|Number)?)[:\s]*([0-9A-Za-z]{15})",
        r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b",
    ])

    due_date = find([
        r"due\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})",
        r"due\s*date[:\s]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        r"due\s*date[:\s]+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
        r"payment\s*due[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})",
    ])

    due_amount_str = find([
        r"due\s*amount[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"amount\s*due[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"balance\s*due[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
    ])

    total_str = find([
        r"total\s*amount[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"grand\s*total[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"amount\s*payable[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"net\s*amount[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"(?:₹|\$)\s*([\d,]+\.\d{2})",
    ])

    try:
        due_amount = float(due_amount_str.replace(",", "")) if due_amount_str else None
    except Exception:
        due_amount = None

    try:
        total = float(total_str.replace(",", "")) if total_str else None
    except Exception:
        total = None

    currency = "INR"
    if re.search(r"\b€|EUR\b", text):   currency = "EUR"
    elif re.search(r"\b£|GBP\b", text): currency = "GBP"
    elif re.search(r"\$|USD", text):    currency = "USD"
    elif re.search(r"₹|INR|Rs\.", text): currency = "INR"

    return {
        "vendor_name":    vendor,
        "client_name":    client_name,
        "invoice_number": invoice_no,
        "invoice_date":   invoice_date,
        "due_date":       due_date,
        "gst_number":     gst_number,
        "total_amount":   total,
        "due_amount":     due_amount,
        "currency":       currency,
    }