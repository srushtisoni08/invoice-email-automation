from pathlib import Path
from utils.helpers import decode_mime_str
from config import ATTACHMENTS_DIR


def save_attachment(part, email_id):

    filename = part.get_filename()

    if not filename:
        return None

    filename = decode_mime_str(filename)

    ext = Path(filename).suffix.lower()

    if ext not in [".pdf", ".xls", ".xlsx"]:
        return None

    path = ATTACHMENTS_DIR / f"{email_id}_{filename}"

    with open(path, "wb") as f:
        f.write(part.get_payload(decode=True))

    return path