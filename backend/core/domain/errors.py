"""Domain error tree.

Every error carries a stable ``code`` that the API's exception handler maps to an HTTP
status exactly once (LLD §8.5). Nothing in the domain knows what an HTTP status is.
"""

from typing import Any


class DomainError(Exception):
    code = "domain_error"
    default_message = "A domain rule was violated."

    def __init__(self, message: str | None = None, **details: Any) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"


# --- not found -------------------------------------------------------------


class NotFoundError(DomainError):
    code = "not_found"
    default_message = "The requested resource does not exist."


class PostNotFound(NotFoundError):
    code = "post_not_found"
    default_message = "This report does not exist."


class UserNotFound(NotFoundError):
    code = "user_not_found"
    default_message = "This user does not exist."


class ContactPageNotFound(NotFoundError):
    code = "contact_page_not_found"
    default_message = "The contact page has not been configured."


# --- conflict --------------------------------------------------------------


class ConflictError(DomainError):
    code = "conflict"
    default_message = "This conflicts with existing data."


class UsernameTaken(ConflictError):
    code = "username_taken"
    default_message = "This username is already registered."


class EmailTaken(ConflictError):
    code = "email_taken"
    default_message = "This email is already registered."


class AlreadyLiked(ConflictError):
    code = "already_liked"
    default_message = "You have already liked this report."


class NotLiked(ConflictError):
    code = "not_liked"
    default_message = "You have not liked this report."


class SelfLikeNotAllowed(ConflictError):
    code = "self_like_not_allowed"
    default_message = "You cannot like your own report."


# --- validation ------------------------------------------------------------


class ValidationError(DomainError):
    code = "validation_error"
    default_message = "The supplied data is invalid."


class InvalidLocation(ValidationError):
    code = "invalid_location"
    default_message = "Coordinates are out of range."


class InvalidRating(ValidationError):
    code = "invalid_rating"
    default_message = "Rating must be between 1 and 5."


# --- authentication --------------------------------------------------------


class AuthenticationError(DomainError):
    code = "authentication_error"
    default_message = "Authentication failed."


class InvalidCredentials(AuthenticationError):
    code = "invalid_credentials"
    default_message = "Incorrect username or password."


class OTPInvalid(AuthenticationError):
    code = "otp_invalid"
    default_message = "This code is not valid."


class OTPExpired(AuthenticationError):
    code = "otp_expired"
    default_message = "This code has expired."


class InvalidToken(AuthenticationError):
    code = "invalid_token"
    default_message = "This token is invalid or has expired."


# --- authorization ---------------------------------------------------------


class AuthorizationError(DomainError):
    code = "authorization_error"
    default_message = "You are not allowed to do this."


class NotAuthorized(AuthorizationError):
    code = "not_authorized"
    default_message = "You are not allowed to do this."


class AccountNotVerified(AuthorizationError):
    code = "account_not_verified"
    default_message = "Verify your account before signing in."


class AccountDisabled(AuthorizationError):
    code = "account_disabled"
    default_message = "This account has been disabled."


# --- infrastructure --------------------------------------------------------


class InfrastructureError(DomainError):
    """Raised by adapters when an external system fails.

    Lives in the domain so use cases can catch it without importing an adapter.
    """

    code = "infrastructure_error"
    default_message = "An external service failed."


class ImageUploadFailed(InfrastructureError):
    code = "image_upload_failed"
    default_message = "The photo could not be uploaded."


class ImageDeleteFailed(InfrastructureError):
    code = "image_delete_failed"
    default_message = "The photo could not be deleted."


class NotificationFailed(InfrastructureError):
    code = "notification_failed"
    default_message = "The message could not be sent."
