from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pathlib import Path

EXCEL_OUTPUT = Path("invoices.xlsx")
HEADERS = [
"Vendor Name",
"Client Name",
"Invoice Number",
"Invoice Date",
"Due Date",
"GST Number",
"Total Amount",
"Due Amount",
"Currency",
"Source File",
"Processed At"
]

def init_excel():
    """Create invoices.xlsx with headers and formatting if it doesn't exist."""
    if EXCEL_OUTPUT.exists():
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"

    header_fill = PatternFill("solid", start_color="1F4E79")
    header_font = Font(bold=True, color="FFFFFF", name="Arial", size=11)
    border = Border(
        bottom=Side(style="thin", color="FFFFFF"),
        right=Side(style="thin", color="FFFFFF"),
    )

    for col, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    col_widths = [25, 20, 18, 18, 12, 35, 22]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"
    wb.save(EXCEL_OUTPUT)
    print(f"[Excel] Created {EXCEL_OUTPUT}")


def append_to_excel(record: dict):
    """Append one invoice record; alternate row shading."""
    wb = load_workbook(EXCEL_OUTPUT)
    ws = wb.active
    next_row = ws.max_row + 1

    fill = PatternFill("solid", start_color="D6E4F0" if next_row % 2 == 0 else "FFFFFF")
    font = Font(name="Arial", size=10)

    values = [
        record.get("vendor_name", ""),
        record.get("client_name", ""),
        record.get("invoice_number", ""),
        record.get("invoice_date", ""),
        record.get("due_date", ""),
        record.get("gst_number", ""),
        record.get("total_amount", ""),
        record.get("due_amount", ""),
        record.get("currency", "USD"),
        record.get("source_file", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ]

    for col, val in enumerate(values, 1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.font = font
        cell.fill = fill
        cell.alignment = Alignment(vertical="center")

    # Keep a running total formula in the row below data
    # Auto-detect column index from HEADERS so it never breaks if columns are reordered
    total_col = HEADERS.index("Total Amount") + 1  # 1-based column index
    total_col_letter = ws.cell(row=1, column=total_col).column_letter
    data_end_row = ws.max_row  # current last data row
    summary_row = data_end_row + 2
    ws.cell(row=summary_row, column=total_col - 1, value="Grand Total").font = Font(bold=True, name="Arial")
    ws.cell(row=summary_row, column=total_col,
            value=f"=SUM({total_col_letter}2:{total_col_letter}{data_end_row})").font = Font(bold=True, name="Arial")

    wb.save(EXCEL_OUTPUT)
    print(f"[Excel] Saved invoice → row {next_row}")