import imaplib
import email
import os
from dotenv import load_dotenv
import pdfplumber
import re
import pandas as pd
import schedule
import time

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL_USER, EMAIL_PASS)

mail.select("inbox")

status, messages = mail.search(None, "UNSEEN")
email_ids = messages[0].split()

for e in email_ids:
    status, msg_data = mail.fetch(e, "(RFC822)")

    for response_part in msg_data:
        if isinstance(response_part, tuple):

            msg = email.message_from_bytes(response_part[1])

            for part in msg.walk():

                if part.get_content_disposition() == "attachment":

                    filename = part.get_filename()
                    filepath = f"data/invoices/{filename}"

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    print("Saved:", filepath)

                    # PROCESS THE SAME FILE
                    with pdfplumber.open(filepath) as pdf:

                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text()

                    invoice_number = re.search(r"Invoice\s*No[:\s]*([A-Z0-9-]+)", text)
                    date = re.search(r"Date[:\s]*([\d/]+)", text)
                    amount = re.search(r"Total[:\s]*\$?([\d,.]+)", text)

                    data = {
                        "invoice_number": invoice_number.group(1) if invoice_number else None,
                        "date": date.group(1) if date else None,
                        "amount": amount.group(1) if amount else None
                    }

                    df = pd.DataFrame([data])

                    if os.path.exists("invoice_data.xlsx"):
                        existing = pd.read_excel("invoice_data.xlsx")
                        df = pd.concat([existing, df])

                    df.to_excel("invoice_data.xlsx", index=False)

                    print("Invoice processed")

# with pdfplumber.open("invoice.pdf") as pdf:
#     text = ""

#     for page in pdf.pages:
#         text += page.extract_text()

# invoice_number = re.search(r"Invoice\s*No[:\s]*([A-Z0-9-]+)", text)

# date = re.search(r"Date[:\s]*([\d/]+)", text)

# amount = re.search(r"Total[:\s]*\$?([\d,.]+)", text)

# data = {
#     "invoice_number": invoice_number.group(1),
#     "date": date.group(1),
#     "amount": amount.group(1)
# }
# df = pd.DataFrame([data])

# df.to_excel("invoice_data.xlsx", index=False)
# existing = pd.read_excel("invoice_data.xlsx")

# df = pd.concat([existing, df])

# df.to_excel("invoice_data.xlsx", index=False)
# print("done")