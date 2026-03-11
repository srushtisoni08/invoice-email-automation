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

    # ── Vendor ────────────────────────────────────────────────────────────────
    # Must match "Vendor Name: <value>" — NOT "Vendor Information"
    # Require a colon after the label keyword so section headings are skipped.
    vendor = find([
        r"vendor\s*name\s*:\s*([A-Za-z0-9 ,.&'()-]{3,80})",
        r"supplier\s*name\s*:\s*([A-Za-z0-9 ,.&'()-]{3,80})",
        r"(?:sold\s*by|billed\s*by|from)\s*:\s*([A-Za-z0-9 ,.&'()-]{3,80})",
        # last resort: first bold/caps line at top of document
        r"^([A-Z][A-Za-z0-9 ,.&'()-]{3,60})\n",
    ])

    # ── Client ────────────────────────────────────────────────────────────────
    # "Client Name: <value>" — NOT just "Client Name" as a label heading
    # Require colon; also handle "Bill To\nClient Name: <value>" layout.
    client_name = find([
        r"client\s*name\s*:\s*([A-Za-z0-9 ,.&'()-]{3,80})",
        r"customer\s*name\s*:\s*([A-Za-z0-9 ,.&'()-]{3,80})",
        r"bill(?:ed)?\s*to\s*\n\s*([A-Za-z0-9 ,.&'()-]{3,80})",
        r"bill(?:ed)?\s*to\s*:\s*([A-Za-z0-9 ,.&'()-]{3,80})",
    ])

    # ── Invoice Number ────────────────────────────────────────────────────────
    invoice_no = find([
        r"invoice\s*(?:no|number|#|id)[.:\s]*([A-Z0-9\-/]{3,30})",
        r"inv[.\s]*#?\s*([A-Z0-9\-/]{3,30})",
    ])

    # ── Invoice Date ──────────────────────────────────────────────────────────
    invoice_date = find([
        r"invoice\s*date\s*:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"invoice\s*date\s*:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        r"invoice\s*date\s*:\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
    ])

    # ── Due Date ──────────────────────────────────────────────────────────────
    due_date = find([
        r"due\s*date\s*:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"due\s*date\s*:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        r"due\s*date\s*:\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
        r"payment\s*due\s*:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ])

    # ── GST Number ────────────────────────────────────────────────────────────
    gst_number = find([
        r"(?:GSTIN|GST\s*No\.?|GST\s*Number)\s*:\s*([0-9A-Za-z]{15})",
        r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b",
    ])

    # ── Total Amount ──────────────────────────────────────────────────────────
    amount_str = find([
        r"(?:grand\s*total|total\s*amount|amount\s*payable)\s*:\s*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"(?:net\s*amount|total)\s*:\s*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
        r"[₹$]\s*([\d,]+\.\d{2})",
    ])

    # ── Due Amount ────────────────────────────────────────────────────────────
    due_amount_str = find([
        r"(?:amount\s*due|balance\s*due|due\s*amount)\s*:\s*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})",
    ])

    try:
        total = float(amount_str.replace(",", "")) if amount_str else None
    except ValueError:
        total = None

    try:
        due_amount = float(due_amount_str.replace(",", "")) if due_amount_str else None
    except ValueError:
        due_amount = None

    # ── Currency ──────────────────────────────────────────────────────────────
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