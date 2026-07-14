import os
import io
from PIL import Image, ImageOps
import json
import base64
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Configuration
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "file.json"
FOLDER_ID = "143-8VgTr2KPveoPtcJ4s2SZGrT1w8Vth"  # Drive folder ID

# Authenticate using local file or env
creds = None
try:
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print("✅ Authenticated using local JSON file.")
    else:
        google_creds_b64 = os.getenv("GOOGLE_CREDENTIALS")
        if not google_creds_b64:
            raise Exception("No credentials file or GOOGLE_CREDENTIALS_B64 environment variable found.")
        # Decode base64 to JSON
        decoded_json = base64.b64decode(google_creds_b64).decode("utf-8")
        google_creds_json = json.loads(decoded_json)
        creds = Credentials.from_service_account_info(google_creds_json, scopes=SCOPES)
        print("✅ Authenticated using base64 credentials from environment.")
except Exception as e:
    print(f"❌ Error in authentication: {str(e)}")
    raise

# Build Drive service
drive_service = build("drive", "v3", credentials=creds)

def upload_to_drive(base64_image: str, filename: str) -> dict | None:
    """
    Upload a base64-encoded image to a Google Drive folder as a square image.
    
    Args:
        base64_image (str): Base64 string with header (e.g., "data:image/png;base64,...")
        filename (str): Desired filename (with or without extension)
    
    Returns:
        dict: Uploaded file metadata or None if failed
    """
    try:
        if ';base64,' not in base64_image:
            raise ValueError("Invalid base64 image format. Missing header.")

        header, data = base64_image.split(';base64,')
        file_ext = header.split('/')[-1].strip()
        if '.' not in filename:
            filename += f".{file_ext}"

        # Decode base64 image data
        file_data = base64.b64decode(data)
        image = Image.open(io.BytesIO(file_data)).convert("RGBA")

        # Make the image square (resize and pad/crop)
        size = max(image.size)
        square_image = Image.new("RGBA", (size, size), (255, 255, 255, 0))  # Transparent background
        square_image.paste(
            image, ((size - image.width) // 2, (size - image.height) // 2)
        )

        # Save to in-memory file
        output_io = io.BytesIO()
        square_image.save(output_io, format=file_ext.upper())
        output_io.seek(0)

        mimetype = f'image/{file_ext}'
        media = MediaIoBaseUpload(output_io, mimetype=mimetype, resumable=True)

        file_metadata = {
            'name': filename,
            'mimeType': mimetype,
            'parents': [FOLDER_ID]  # Replace with your folder ID
        }

        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()

        print("✅ Upload successful:", uploaded_file)
        return uploaded_file

    except Exception as e:
        print("❌ Upload failed:", str(e))
        return None
    
def delete_from_drive(file_id: str) -> bool:
    """
    Delete a file from Google Drive by its file ID.

    Args:
        file_id (str): The ID of the file to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    try:
        drive_service.files().delete(fileId=file_id).execute()
        print(f"✅ File with ID {file_id} deleted successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to delete file with ID {file_id}: {e}")
        return False