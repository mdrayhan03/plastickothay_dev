"""Google Drive image storage - the production ImageStorage adapter.

Ports the legacy backend_old/fileupload.py behind the port, with two changes:
  - takes decoded bytes, not a base64 string (base64 is decoded at the serializer, LLD §7.1)
  - the Drive client is built lazily, so importing this module needs no credentials - the
    container only instantiates it when GOOGLE_CREDENTIALS is configured.

Auth: a service-account JSON file (GOOGLE_SERVICE_ACCOUNT_FILE) or base64 JSON in the
GOOGLE_CREDENTIALS env var, matching the legacy behaviour.
"""

import base64
import io
import json
import os

from core.domain.errors import ImageDeleteFailed, ImageUploadFailed
from core.domain.value_objects import ImageRef
from core.ports.storage import ImageStorage

PROVIDER = "gdrive"
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "143-8VgTr2KPveoPtcJ4s2SZGrT1w8Vth")
TIMEOUT = int(os.getenv("GOOGLE_DRIVE_TIMEOUT", "30"))  # seconds - no Celery, so cap the hang


def _credentials():
    from google.oauth2.service_account import Credentials

    path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "file.json")
    if os.path.exists(path):
        return Credentials.from_service_account_file(path, scopes=SCOPES)
    b64 = os.getenv("GOOGLE_CREDENTIALS")
    if not b64:
        raise ImageUploadFailed("No Google Drive credentials configured.")
    info = json.loads(base64.b64decode(b64).decode("utf-8"))
    return Credentials.from_service_account_info(info, scopes=SCOPES)


class GoogleDriveImageStorage(ImageStorage):
    def __init__(self) -> None:
        self._service = None  # built lazily on first use

    @property
    def service(self):
        if self._service is None:
            import google_auth_httplib2
            import httplib2
            from googleapiclient.discovery import build

            # Attach a socket timeout to the authorized transport so uploads/deletes can't
            # hang a worker indefinitely. build(http=...) is the documented way to do this
            # with a service account (credentials go on the AuthorizedHttp, not build()).
            authed_http = google_auth_httplib2.AuthorizedHttp(
                _credentials(), http=httplib2.Http(timeout=TIMEOUT)
            )
            self._service = build("drive", "v3", http=authed_http)
        return self._service

    def upload(self, data: bytes, filename: str, content_type: str) -> ImageRef:
        from googleapiclient.http import MediaIoBaseUpload

        try:
            media = MediaIoBaseUpload(
                io.BytesIO(data), mimetype=content_type or "image/jpeg", resumable=True
            )
            uploaded = (
                self.service.files()
                .create(
                    body={"name": filename, "parents": [FOLDER_ID]},
                    media_body=media,
                    fields="id",
                )
                .execute()
            )
        except ImageUploadFailed:
            raise
        except Exception as exc:
            raise ImageUploadFailed(str(exc)) from exc
        return ImageRef(provider=PROVIDER, external_id=uploaded["id"])

    def delete(self, ref: ImageRef) -> None:
        try:
            self.service.files().delete(fileId=ref.external_id).execute()
        except Exception as exc:
            raise ImageDeleteFailed(str(exc)) from exc

    def public_url(self, ref: ImageRef) -> str:
        return f"https://drive.google.com/uc?id={ref.external_id}"
