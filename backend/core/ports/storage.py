"""Image storage port.

Implemented by the Google Drive adapter today. Takes decoded bytes, never a base64 string:
base64 is transport encoding and is decoded at the serializer (LLD §7.1).
"""

from abc import ABC, abstractmethod

from core.domain.value_objects import ImageRef


class ImageStorage(ABC):
    @abstractmethod
    def upload(self, data: bytes, filename: str, content_type: str) -> ImageRef:
        """Raises ImageUploadFailed."""

    @abstractmethod
    def delete(self, ref: ImageRef) -> None:
        """Raises ImageDeleteFailed."""

    @abstractmethod
    def public_url(self, ref: ImageRef) -> str: ...
