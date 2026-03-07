import imaplib
import email
from datetime import datetime
from .attachment_handler import save_attachment
from extractors.pdf_extractor import extract_from_pdf
from extractors.excel_extractor import extract_from_excel
from storage.excel_writer import append_to_excel
from utils.helpers import decode_mime_str
from config import EMAIL_USER, EMAIL_PASS


def check_emails():

    print(f"\n[{datetime.now():%H:%M:%S}] Checking inbox")

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    _, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()

    for eid in email_ids:

        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_mime_str(msg.get("Subject", "(no subject)"))
        print("Subject:", subject)

        for part in msg.walk():

            if part.get_content_disposition() == "attachment":

                path = save_attachment(part, eid.decode())

                if not path:
                    continue

                if path.suffix == ".pdf":
                    data = extract_from_pdf(path)

                elif path.suffix in [".xls", ".xlsx"]:
                    data = extract_from_excel(path)

                else:
                    continue

                data["source_file"] = path.name
                append_to_excel(data)

    mail.logout()