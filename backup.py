import imaplib
import email
import os
from email.utils import parsedate_to_datetime

# -------------------------
# Gmail Settings
# -------------------------

IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = os.environ["GMAIL_EMAIL"]
APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

# -------------------------
# Output folder
# -------------------------

OUTPUT_FOLDER = "Journal"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -------------------------
# Connect to Gmail
# -------------------------

mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL_ACCOUNT, APP_PASSWORD)

mail.select("inbox")

# Only unread emails with subject exactly "1"
status, messages = mail.search(None, '(UNSEEN SUBJECT "1")')

mail_ids = messages[0].split()

print("Matching emails:", len(mail_ids))

for num in mail_ids:

    status, msg_data = mail.fetch(num, "(RFC822)")

    for response in msg_data:

        if not isinstance(response, tuple):
            continue

        msg = email.message_from_bytes(response[1])

        subject = (msg["subject"] or "").strip()

        if subject != "1":
            continue

        body = ""

        if msg.is_multipart():

            for part in msg.walk():

                if (
                    part.get_content_type() == "text/plain"
                    and part.get("Content-Disposition") is None
                ):
                    body = part.get_payload(decode=True).decode(
                        errors="ignore"
                    )
                    break

        else:

            body = msg.get_payload(decode=True).decode(
                errors="ignore"
            )

        email_date = parsedate_to_datetime(msg["Date"])

        filename = email_date.strftime(
            "%Y-%m-%d_%H-%M-%S"
        ) + ".md"

        filepath = os.path.join(
            OUTPUT_FOLDER,
            filename
        )

        # Skip duplicates
        if os.path.exists(filepath):
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(body)

        print("Saved:", filename)

        # Mark email as read
        mail.store(
            num,
            "+FLAGS",
            "\\Seen"
        )

mail.logout()