"""Shared avatar handling for registration and profile updates."""

from core.application.accounts.dto import Avatar
from core.domain.value_objects import ImageRef
from core.ports.storage import ImageStorage


def upload_avatar(images: ImageStorage | None, avatar: Avatar | None) -> ImageRef | None:
    """Upload a decoded avatar and return its ref, or None when there's nothing to store
    (no avatar supplied, or no storage wired — e.g. in fast unit tests)."""
    if avatar is None or images is None:
        return None
    return images.upload(avatar.data, avatar.filename, avatar.content_type)
