import imaplib
import email
import io
import os
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# -------------------------
# Gmail Settings
# -------------------------

IMAP_SERVER = "imap.gmail.com"

EMAIL_ACCOUNT = os.environ["GMAIL_EMAIL"]
APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

# -------------------------
# Google Drive Settings
# -------------------------

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Replace with your Google Drive Journal folder ID
FOLDER_ID = "1oVRt3xY1LN-Ph6JRu6vzFHQIV0ue_0cy"

# -------------------------
# Google OAuth
# -------------------------

creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file(
        "token.json",
        SCOPES
    )

if not creds or not creds.valid:

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES
        )

        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

drive_service = build(
    "drive",
    "v3",
    credentials=creds
)

# -------------------------
# Connect to Gmail
# -------------------------

mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(
    EMAIL_ACCOUNT,
    APP_PASSWORD
)

mail.select("inbox")

# Only unread emails with subject exactly "1"

status, messages = mail.search(
    None,
    '(UNSEEN SUBJECT "1")'
)

mail_ids = messages[0].split()

print("Matching emails:", len(mail_ids))

for num in mail_ids:

    status, msg_data = mail.fetch(
        num,
        "(RFC822)"
    )

    for response in msg_data:

        if not isinstance(response, tuple):
            continue

        msg = email.message_from_bytes(
            response[1]
        )

        subject = (
            msg["subject"] or ""
        ).strip()

        if subject != "1":
            continue

        body = ""

        if msg.is_multipart():

            for part in msg.walk():

                if (
                    part.get_content_type() == "text/plain"
                    and part.get("Content-Disposition") is None
                ):

                    body = (
                        part.get_payload(decode=True)
                        .decode(errors="ignore")
                    )

                    break

        else:

            body = (
                msg.get_payload(decode=True)
                .decode(errors="ignore")
            )

        email_date = parsedate_to_datetime(
            msg["Date"]
        )

        filename = (
            email_date.strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            + ".md"
        )

        # Check if file already exists in Drive

        query = (
            f"name='{filename}' "
            f"and '{FOLDER_ID}' in parents "
            f"and trashed=false"
        )

        existing = (
            drive_service.files()
            .list(
                q=query,
                fields="files(id,name)"
            )
            .execute()
        )

        if existing.get("files"):
            print("Already exists:", filename)

            mail.store(
                num,
                "+FLAGS",
                "\\Seen"
            )

            continue

        file_metadata = {
            "name": filename,
            "parents": [FOLDER_ID]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(
                body.encode("utf-8")
            ),
            mimetype="text/markdown"
        )

        drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        print("Uploaded:", filename)

        mail.store(
            num,
            "+FLAGS",
            "\\Seen"
        )

mail.logout()