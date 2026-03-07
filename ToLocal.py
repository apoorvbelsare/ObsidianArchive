import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import io

# -------------------------
# Google Drive settings
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER_ID = "1oVRt3xY1LN-Ph6JRu6vzFHQIV0ue_0cy"

# Local folder where notes will be stored
LOCAL_FOLDER = r"D:\ObsidianVault\EmailNotes"

# -------------------------
# Authentication
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

service = build("drive", "v3", credentials=creds)

os.makedirs(LOCAL_FOLDER, exist_ok=True)

# -------------------------
# List files in Drive folder
# -------------------------
query = f"'{FOLDER_ID}' in parents and mimeType='text/markdown'"

results = service.files().list(
    q=query,
    fields="files(id, name)"
).execute()

files = results.get("files", [])

print("Files found:", len(files))

for file in files:

    file_name = file["name"]
    file_id = file["id"]

    local_path = os.path.join(LOCAL_FOLDER, file_name)

    # Skip if file already exists
    if os.path.exists(local_path):
        continue

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, "wb")

    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()

    print("Downloaded:", file_name)