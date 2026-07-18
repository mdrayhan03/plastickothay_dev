"""Password hashing via Django's configured hashers.

The PasswordHasher port exists so use cases never import django.contrib.auth. This adapter is
the only place that dependency lives.
"""

from django.contrib.auth.hashers import check_password, make_password

from core.ports.security import PasswordHasher


class DjangoPasswordHasher(PasswordHasher):
    def hash(self, raw: str) -> str:
        return make_password(raw)

    def verify(self, raw: str, hashed: str) -> bool:
        return check_password(raw, hashed)
