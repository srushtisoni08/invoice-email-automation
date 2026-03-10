import imaplib
import email
import traceback
from datetime import datetime
from .attachment_handler import save_attachment
from extractors.pdf_extractor import extract_from_pdf
from extractors.excel_extractor import extract_from_excel
from extractors.body_extractor import extract_from_body
from storage.excel_writer import append_to_excel
from utils.helpers import decode_mime_str
from config import EMAIL_USER, EMAIL_PASS

IMAP_TIMEOUT = 30

def check_emails():

    print(f"\n[{datetime.now():%H:%M:%S}] Checking inbox")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=IMAP_TIMEOUT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        _, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()

        if not email_ids:
            print("[Info] No new emails found.")
            mail.logout()
            return

        print(f"[Info] Found {len(email_ids)} new email(s).")

        for eid in email_ids:

            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = decode_mime_str(msg.get("Subject", "(no subject)"))
            print(f"[Email] Subject: {subject}")

            mail.store(eid, "+FLAGS", "\\Seen")

            found_attachment = False
            body_text = ""

            for part in msg.walk():
                content_type = part.get_content_type()

                if content_type == "text/plain" and part.get_content_disposition() != "attachment":
                    try:
                        raw = part.get_payload(decode=True)
                        if raw is not None:
                            body_text += raw.decode("utf-8", errors="ignore")
                    except Exception:
                        pass

                if part.get_content_disposition() == "attachment":

                    path = save_attachment(part, eid.decode())

                    if not path:
                        continue

                    found_attachment = True

                    if path.suffix == ".pdf":
                        attachment_data = extract_from_pdf(path)

                    elif path.suffix in [".xls", ".xlsx"]:
                        attachment_data = extract_from_excel(path)

                    else:
                        print(f"[Skip] Unsupported file type: {path.suffix}")
                        continue

                    # FIX 1: Merge body fields into attachment data for any
                    # fields the attachment extractor could not find.
                    # Body text often contains Client Name, GST, Due Date etc.
                    # that are not inside the PDF/Excel file itself.
                    if body_text.strip():
                        body_data = extract_from_body(body_text)
                        for key, val in body_data.items():
                            # Only fill in missing/empty fields from body
                            if not attachment_data.get(key) and val:
                                attachment_data[key] = val
                                print(f"[Merge] '{key}' filled from email body")

                    attachment_data["source_file"] = path.name
                    append_to_excel(attachment_data)
                    print(f"[Done] Invoice saved from attachment: {path.name}")

            # FIX 2: Only fall back to body-only extraction when truly no
            # supported attachment was found (original logic was correct here,
            # but now body_text is also used for merging above).
            if not found_attachment:
                if body_text.strip():
                    data = extract_from_body(body_text)
                    if any(data.get(k) for k in ["vendor_name", "invoice_number", "total_amount"]):
                        data["source_file"] = f"email_body_{eid.decode()}"
                        append_to_excel(data)
                        print(f"[Done] Invoice extracted from email body: '{subject}'")
                    else:
                        print(f"[Warning] No invoice data found in body or attachment for: '{subject}'")
                else:
                    print(f"[Warning] No supported attachment and no body text in: '{subject}'")

        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"[IMAP Error] {e}")
    except Exception as e:
        print(f"[Error] Unexpected error in check_emails: {e}")
        traceback.print_exc()