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

            # Mark as SEEN immediately so next loop does not re-process it
            mail.store(eid, "+FLAGS", "\\Seen")

            found_attachment = False
            body_text = ""

            for part in msg.walk():
                content_type = part.get_content_type()

                # get_payload(decode=True) returns None for multipart container parts
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
                        data = extract_from_pdf(path)

                    elif path.suffix in [".xls", ".xlsx"]:
                        data = extract_from_excel(path)

                    else:
                        print(f"[Skip] Unsupported file type: {path.suffix}")
                        continue

                    data["source_file"] = path.name
                    append_to_excel(data)
                    print(f"[Done] Invoice saved from attachment: {path.name}")

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
        # Full traceback so you can see exact file + line number next time
        print(f"[Error] Unexpected error in check_emails: {e}")
        traceback.print_exc()