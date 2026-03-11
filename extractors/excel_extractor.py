"""
excel_extractor.py
------------------
Handles TWO Excel invoice layouts:

  1. TABLE layout  — row 1 = headers, rows 2-N = data (one invoice per row)
     Example:
       Vendor Name | Invoice Number | Invoice Date | ...
       TechNova    | INV-001        | 2026-03-11   | ...
       DataEdge    | INV-002        | 2026-03-12   | ...

  2. FORM layout   — label in col A, value in col B (or value below label)
     Example:
       Vendor Name  | TechNova Solutions
       Invoice No   | INV-001
       Invoice Date | 2026-03-11

Returns a LIST of dicts (one per invoice row found).
For backward compatibility, extract_from_excel() still returns a single dict
(the first invoice) — use extract_all_from_excel() to get all rows.
"""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime, date as date_type


# ─────────────────────────── helpers ──────────────────────────────────────────

def _fmt_date(val) -> str:
    """Convert any cell value to DD-MM-YYYY string, or '' if not date-like."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, (datetime, date_type)):
        return val.strftime("%d-%m-%Y")
    if isinstance(val, (int, float)):
        try:
            ts = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(val))
            if 1990 <= ts.year <= 2100:
                return ts.strftime("%d-%m-%Y")
        except Exception:
            pass
    s = str(val).strip()
    # YYYY-MM-DD  (ISO format from Excel)
    m = re.match(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$", s)
    if m:
        y, mo, d_ = m.groups()
        return f"{int(d_):02d}-{int(mo):02d}-{y}"
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$", s)
    if m:
        d_, mo, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(d_):02d}-{int(mo):02d}-{y}"
    return ""


def _fmt_amount(val):
    """Return float or None."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = re.sub(r"[₹$€£,\s]", "", str(val))
    try:
        return float(s)
    except ValueError:
        return None


def _is_empty(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def _detect_currency(df: pd.DataFrame) -> str:
    text = " ".join(str(v) for v in df.values.flatten() if not _is_empty(v))
    if re.search(r"₹|INR|Rs\.", text):  return "INR"
    if re.search(r"\$|USD", text):      return "USD"
    if re.search(r"€|EUR", text):       return "EUR"
    if re.search(r"£|GBP", text):       return "GBP"
    return "INR"


# ─────────────── column-name → field mapping (TABLE layout) ───────────────────

_COL_MAP = {
    "vendor_name":    re.compile(r"vendor|supplier|seller|company\s*name|billed\s*by", re.I),
    "client_name":    re.compile(r"client|customer|bill(?:ed)?\s*to|buyer", re.I),
    "invoice_number": re.compile(r"invoice\s*(?:no|number|#|id)|inv\s*(?:no|#)", re.I),
    "due_date":       re.compile(r"due\s*date|payment\s*due", re.I),
    "invoice_date":   re.compile(r"invoice\s*date|date\s*of\s*invoice|(?<!\w)date(?!\s*due)", re.I),
    "gst_number":     re.compile(r"gstin|gst\s*(?:no|number|#)|tax\s*id", re.I),
    "total_amount":   re.compile(r"total\s*amount|grand\s*total|amount\s*payable|net\s*amount|(?<!\w)total(?!\s*tax)", re.I),
    "due_amount":     re.compile(r"due\s*amount|amount\s*due|balance\s*due", re.I),
}

_DATE_FIELDS   = {"invoice_date", "due_date"}
_AMOUNT_FIELDS = {"total_amount", "due_amount"}


def _map_columns(columns) -> dict:
    """Return {field: col_index} for every header that matches a known field."""
    mapping = {}
    for idx, col in enumerate(columns):
        col_str = str(col).strip()
        for field, pat in _COL_MAP.items():
            if field not in mapping and pat.search(col_str):
                mapping[field] = idx
                break
    return mapping


def _is_table_layout(df: pd.DataFrame) -> bool:
    """
    True when row 0 looks like a header row (≥3 cells match known field patterns).
    """
    if df.shape[0] < 2:
        return False
    header_row = df.iloc[0]
    matches = sum(
        1 for v in header_row
        if not _is_empty(v) and any(p.search(str(v)) for p in _COL_MAP.values())
    )
    return matches >= 3


# ─────────────── TABLE layout extractor ───────────────────────────────────────

def _extract_table(df: pd.DataFrame, currency: str) -> list[dict]:
    """Extract one dict per data row from a table-format sheet."""
    headers = list(df.iloc[0])
    col_map = _map_columns(headers)

    if not col_map:
        return []

    records = []
    for row_idx in range(1, len(df)):
        row = df.iloc[row_idx]

        # Skip completely empty rows
        if all(_is_empty(v) for v in row):
            continue

        rec = {
            "vendor_name":    "",
            "client_name":    "",
            "invoice_number": "",
            "invoice_date":   "",
            "due_date":       "",
            "gst_number":     "",
            "total_amount":   None,
            "due_amount":     None,
            "currency":       currency,
        }

        for field, col_idx in col_map.items():
            raw = row.iloc[col_idx]
            if _is_empty(raw):
                continue
            if field in _DATE_FIELDS:
                rec[field] = _fmt_date(raw)
            elif field in _AMOUNT_FIELDS:
                rec[field] = _fmt_amount(raw)
            else:
                rec[field] = str(raw).strip()

        records.append(rec)
        print(f"[Excel] Row {row_idx}: invoice_number={rec['invoice_number']!r}  vendor={rec['vendor_name']!r}")

    return records


# ─────────────── FORM layout extractor (original logic) ───────────────────────

def _looks_like_label(v) -> bool:
    if _is_empty(v) or isinstance(v, (int, float, datetime, date_type)):
        return False
    return bool(re.search(
        r"vendor|supplier|client|customer|invoice|bill|due|gst|gstin|total|amount|date|currency|tax",
        str(v), re.I
    ))


def _extract_pairs(df: pd.DataFrame):
    arr = df.values
    rows, cols = arr.shape
    for r in range(rows):
        for c in range(cols):
            cell = arr[r, c]
            if not _looks_like_label(cell):
                continue
            label = str(cell).strip()
            if c + 1 < cols:
                right = arr[r, c + 1]
                if not _is_empty(right) and not _looks_like_label(right):
                    yield (label, right)
                    continue
            if r + 1 < rows:
                below = arr[r + 1, c]
                if not _is_empty(below) and not _looks_like_label(below):
                    yield (label, below)


_FORM_PATTERNS = {
    "vendor_name":    re.compile(r"vendor|supplier|seller|billed\s*by|(?<!\w)from(?!\w)|company\s*name", re.I),
    "client_name":    re.compile(r"client|customer|bill(?:ed)?\s*to|ship(?:ped)?\s*to|buyer", re.I),
    "invoice_number": re.compile(r"invoice\s*(?:no|number|#|id)|inv\s*(?:no|#)", re.I),
    "due_date":       re.compile(r"due\s*date|payment\s*due|expiry\s*date", re.I),
    "invoice_date":   re.compile(r"invoice\s*date|date\s*of\s*invoice|(?<!\w)date(?!\s*due)", re.I),
    "gst_number":     re.compile(r"gstin|gst\s*(?:no|number|#)|tax\s*id", re.I),
    "total_amount":   re.compile(r"total\s*amount|grand\s*total|amount\s*payable|net\s*amount|(?<!\w)total(?!\s*tax)", re.I),
    "due_amount":     re.compile(r"due\s*amount|amount\s*due|balance\s*due", re.I),
}


def _match_form_field(label: str):
    for field, pat in _FORM_PATTERNS.items():
        if pat.search(label):
            return field
    return None


def _extract_form(df: pd.DataFrame, currency: str) -> list[dict]:
    rec = {
        "vendor_name":    "",
        "client_name":    "",
        "invoice_number": "",
        "invoice_date":   "",
        "due_date":       "",
        "gst_number":     "",
        "total_amount":   None,
        "due_amount":     None,
        "currency":       currency,
    }
    for label, raw_val in _extract_pairs(df):
        field = _match_form_field(label)
        if not field:
            continue
        if field in _AMOUNT_FIELDS and rec[field] is not None:
            continue
        if field not in _AMOUNT_FIELDS and rec[field]:
            continue
        if field in _DATE_FIELDS:
            v = _fmt_date(raw_val)
            if v:
                rec[field] = v
                print(f"[Excel] {field} = {v!r}")
        elif field in _AMOUNT_FIELDS:
            v = _fmt_amount(raw_val)
            if v is not None:
                rec[field] = v
                print(f"[Excel] {field} = {v}")
        else:
            s = str(raw_val).strip()
            if s and not re.match(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}", s):
                rec[field] = s
                print(f"[Excel] {field} = {s!r}")
    return [rec]


# ─────────────── regex fallback ───────────────────────────────────────────────

def _regex_fallback(text: str, rec: dict) -> dict:
    def find(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    if not rec["vendor_name"]:
        rec["vendor_name"] = find([r"vendor\s*(?:name)?[:\s]+(.+)"])
    if not rec["invoice_number"]:
        rec["invoice_number"] = find([r"invoice\s*(?:no|#|number)[:\s]+([A-Z0-9\-/]+)"])
    if not rec["invoice_date"]:
        raw = find([r"invoice\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})"])
        rec["invoice_date"] = _fmt_date(raw) if raw else ""
    if not rec["due_date"]:
        raw = find([r"due\s*date[:\s]+(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})"])
        rec["due_date"] = _fmt_date(raw) if raw else ""
    if not rec["gst_number"]:
        rec["gst_number"] = find([
            r"(?:GSTIN|GST\s*(?:No\.?|Number)?)[:\s]*([0-9A-Za-z]{15})",
            r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b",
        ])
    if rec["total_amount"] is None:
        raw = find([r"(?:total\s*amount|grand\s*total)[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})"])
        rec["total_amount"] = _fmt_amount(raw) if raw else None
    if rec["due_amount"] is None:
        raw = find([r"(?:due\s*amount|amount\s*due)[:\s]*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+\.?\d{0,2})"])
        rec["due_amount"] = _fmt_amount(raw) if raw else None
    return rec


# ─────────────── public API ───────────────────────────────────────────────────

def extract_all_from_excel(path: Path) -> list[dict]:
    """
    Extract ALL invoice rows from an Excel file.
    Returns a list of dicts — one per invoice found.
    """
    try:
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
        all_dfs = list(sheets.values())
    except Exception as e:
        print(f"[Excel] Could not read {path.name}: {e}")
        return []

    all_records = []
    for df in all_dfs:
        currency = _detect_currency(df)
        if _is_table_layout(df):
            print(f"[Excel] Detected TABLE layout — {len(df)-1} data row(s)")
            records = _extract_table(df, currency)
        else:
            print(f"[Excel] Detected FORM layout")
            records = _extract_form(df, currency)

        # Regex fallback on each record
        flat_text = df.to_string(index=False, header=False)
        for rec in records:
            _regex_fallback(flat_text, rec)

        all_records.extend(records)

    return all_records


def extract_from_excel(path: Path) -> dict:
    """
    Backward-compatible: returns the FIRST invoice dict found.
    (email_client.py calls this; it then calls append_to_excel once.)
    Use extract_all_from_excel() when you need all rows.
    """
    records = extract_all_from_excel(path)
    if not records:
        return {
            "vendor_name": "", "client_name": "", "invoice_number": "",
            "invoice_date": "", "due_date": "", "gst_number": "",
            "total_amount": None, "due_amount": None, "currency": "INR",
        }
    return records[0]