from email.header import decode_header


def decode_mime_str(value):

    parts = decode_header(value)

    return "".join(
        t.decode(enc or "utf-8") if isinstance(t, bytes) else t
        for t, enc in parts
    )