"""Commands for the accounts use cases."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Avatar:
    """A decoded profile image ready to upload. base64 is decoded at the HTTP edge."""

    data: bytes
    filename: str
    content_type: str


@dataclass(frozen=True, slots=True)
class RegisterCommand:
    username: str
    email: str
    first_name: str
    last_name: str
    phone: str
    password: str
    avatar: Avatar | None = None


@dataclass(frozen=True, slots=True)
class VerifyOTPCommand:
    username: str
    code: int


@dataclass(frozen=True, slots=True)
class LoginCommand:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class ResetPasswordCommand:
    username: str
    code: int
    new_password: str


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    avatar: Avatar | None = None
