"""Local filesystem image storage.

The dev/test implementation of the ImageStorage port - no Google credentials required. Files
land under MEDIA_ROOT and are served by Django/Whitenoise. The Drive adapter drops in for prod
by swapping this in the container; nothing above the port changes.
"""

import uuid
from pathlib import Path

from django.conf import settings

from core.domain.errors import ImageDeleteFailed, ImageUploadFailed
from core.domain.value_objects import ImageRef
from core.ports.storage import ImageStorage

PROVIDER = "local"


class LocalImageStorage(ImageStorage):
    def __init__(self) -> None:
        self.root = Path(getattr(settings, "MEDIA_ROOT", Path("media"))) / "reports"
        self.base_url = getattr(settings, "MEDIA_URL", "/media/") + "reports/"

    def upload(self, data: bytes, filename: str, content_type: str) -> ImageRef:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
            external_id = f"{uuid.uuid4()}.{ext}"
            (self.root / external_id).write_bytes(data)
        except Exception as exc:
            raise ImageUploadFailed(str(exc)) from exc
        return ImageRef(provider=PROVIDER, external_id=external_id)

    def delete(self, ref: ImageRef) -> None:
        try:
            target = self.root / ref.external_id
            if target.exists():
                target.unlink()
        except Exception as exc:
            raise ImageDeleteFailed(str(exc)) from exc

    def public_url(self, ref: ImageRef) -> str:
        return f"{self.base_url}{ref.external_id}"
