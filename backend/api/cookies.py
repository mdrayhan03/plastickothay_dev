"""Refresh-token cookie helpers.

The refresh token lives in an httpOnly, Secure, SameSite=Lax cookie scoped to /api/auth/
(LLD §8.1). The access token is returned in the JSON body and kept in memory by the SPA -
never in a cookie, never in localStorage. Same-origin deployment keeps the cookie first-party
(DEC-7), so SameSite=Lax works and CORS is unnecessary.
"""

from django.conf import settings

REFRESH_COOKIE = "refresh_token"
REFRESH_PATH = "/api/auth/"
REFRESH_MAX_AGE = 7 * 24 * 3600  # matches REFRESH_TTL


def set_refresh_cookie(response, refresh_token: str):
    # SameSite comes from settings (REFRESH_COOKIE_SAMESITE): "Lax" same-origin, "None" for a
    # cross-origin deploy. SameSite=None is only valid when Secure, so force Secure in that case.
    samesite = getattr(settings, "REFRESH_COOKIE_SAMESITE", "Lax")
    secure = not settings.DEBUG or samesite.lower() == "none"
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=REFRESH_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=REFRESH_PATH,
    )
    return response


def clear_refresh_cookie(response):
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH)
    return response


def read_refresh_cookie(request) -> str | None:
    return request.COOKIES.get(REFRESH_COOKIE)
