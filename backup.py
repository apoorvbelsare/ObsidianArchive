import imaplib
import email
import io
import os
from email.utils import parsedate_to_datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# -------------------------
# Gmail Settings
# -------------------------
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "obsidian1188@gmail.com"
APP_PASSWORD = "vxiszgonhyohktol"

# -------------------------
# Google Drive Settings
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_ID = "1oVRt3xY1LN-Ph6JRu6vzFHQIV0ue_0cy"

# -------------------------
# Google Drive Authentication
# -------------------------
creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

drive_service = build("drive", "v3", credentials=creds)

# -------------------------
# Connect to Gmail
# -------------------------
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL_ACCOUNT, APP_PASSWORD)

mail.select("inbox")

# Only unread emails containing subject "1"
status, messages = mail.search(None, '(UNSEEN SUBJECT "1")')
mail_ids = messages[0].split()

print("Matching emails:", len(mail_ids))

for num in mail_ids:

    status, msg_data = mail.fetch(num, "(RFC822)")

    for response in msg_data:
        if isinstance(response, tuple):

            msg = email.message_from_bytes(response[1])
            subject = msg["subject"].strip()

            # Only accept subject exactly "1"
            if subject != "1":
                continue

            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            # -------------------------
            # Create filename using email date
            # -------------------------
            email_date = parsedate_to_datetime(msg["date"])
            file_name = email_date.strftime("%Y-%m-%d_%H-%M-%S") + ".md"

            # -------------------------
            # Upload to Google Drive
            # -------------------------
            file_metadata = {
                "name": file_name,
                "parents": [FOLDER_ID]
            }

            media = MediaIoBaseUpload(
                io.BytesIO(body.encode()),
                mimetype="text/markdown"
            )

            drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

            print("Uploaded:", file_name)

            # mark email as read
            mail.store(num, '+FLAGS', '\\Seen')

mail.logout()