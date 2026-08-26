"""Permission matrix - every endpoint × {anonymous, user, staff}.

The design is "IsAuthenticated by default + explicit AllowAny overrides". That is exactly the
shape where one forgotten decorator either breaks the public surface or leaks admin data. This
test is the backstop: it pins the intended access level of every route (LLD §7, §10, DEC -
B7 exit criterion).

`expected` is the status an actor should get. 401/403 = blocked. Anything else = reachable
(the request may still 400/404 on payload/lookup, which is fine - we only assert it wasn't
blocked at the permission layer).
"""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from adapters.persistence.django_orm import models as orm
from core.domain.value_objects import Role

pytestmark = pytest.mark.django_db

BLOCKED = {401, 403}


def _make(client, username, role):
    client.post(
        "/api/auth/register/",
        {
            "username": username,
            "email": f"{username}@e.com",
            "first_name": "N",
            "last_name": "N",
            "phone": "+880",
            "password": "s3cretpass",
        },
        format="json",
    )
    code = int(re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1))
    client.post("/api/auth/verify/", {"username": username, "code": code}, format="json")
    if role is not Role.USER:
        u = orm.User.objects.get(username=username)
        u.is_superuser = role is Role.ADMIN
        u.is_staff = role in (Role.STAFF, Role.ADMIN)
        u.save()
    return client.post(
        "/api/auth/login/", {"username": username, "password": "s3cretpass"}, format="json"
    ).data["access"]


@pytest.fixture
def actors():
    anon = APIClient()
    user = APIClient()
    user.credentials(HTTP_AUTHORIZATION=f"Bearer {_make(user, 'u', Role.USER)}")
    staff = APIClient()
    staff.credentials(HTTP_AUTHORIZATION=f"Bearer {_make(staff, 's', Role.STAFF)}")
    return {"anon": anon, "user": user, "staff": staff}


# (method, path, {actor: should_be_allowed})
PUBLIC = True
DENIED = False

MATRIX = [
    # Public reads/writes - everyone allowed.
    ("get", "/api/posts/", {"anon": PUBLIC, "user": PUBLIC, "staff": PUBLIC}),
    ("get", "/api/map/posts/", {"anon": PUBLIC, "user": PUBLIC, "staff": PUBLIC}),
    ("get", "/api/leaderboard/", {"anon": PUBLIC, "user": PUBLIC, "staff": PUBLIC}),
    ("get", "/api/contact-page/", {"anon": PUBLIC, "user": PUBLIC, "staff": PUBLIC}),
    ("post", "/api/contact-messages/", {"anon": PUBLIC, "user": PUBLIC, "staff": PUBLIC}),
    ("post", "/api/feedback/", {"anon": PUBLIC, "user": PUBLIC, "staff": PUBLIC}),
    # Auth-only.
    ("get", "/api/me/", {"anon": DENIED, "user": PUBLIC, "staff": PUBLIC}),
    ("get", "/api/me/posts/", {"anon": DENIED, "user": PUBLIC, "staff": PUBLIC}),
    ("get", "/api/me/contribution/", {"anon": DENIED, "user": PUBLIC, "staff": PUBLIC}),
    # Admin-only - user must be blocked, staff allowed.
    ("get", "/api/admin/posts/", {"anon": DENIED, "user": DENIED, "staff": PUBLIC}),
    ("get", "/api/admin/stats/", {"anon": DENIED, "user": DENIED, "staff": PUBLIC}),
    ("get", "/api/contact-messages/", {"anon": DENIED, "user": DENIED, "staff": PUBLIC}),
    ("get", "/api/feedback/", {"anon": DENIED, "user": DENIED, "staff": PUBLIC}),
    ("put", "/api/contact-page/", {"anon": DENIED, "user": DENIED, "staff": PUBLIC}),
]


@pytest.mark.parametrize("method,path,expectations", MATRIX)
def test_permission_matrix(actors, method, path, expectations):
    for actor_name, should_allow in expectations.items():
        client = actors[actor_name]
        if method in ("post", "put"):
            resp = getattr(client, method)(path, {}, format="json")
        else:
            resp = getattr(client, method)(path)
        blocked = resp.status_code in BLOCKED
        where = f"{method.upper()} {path} ({resp.status_code})"
        if should_allow:
            assert not blocked, f"{actor_name} should reach {where}"
        else:
            assert blocked, f"{actor_name} must be blocked from {where}"


_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="  # noqa: E501


def test_admin_mutations_blocked_for_regular_user(actors):
    """Moderation actions on a real post: user gets 403, staff reaches the use case."""
    pid = (
        APIClient()
        .post(
            "/api/posts/",
            {
                "severity": 3,
                "lat": 23.8,
                "lon": 90.4,
                "photo": f"data:image/png;base64,{_PNG_B64}",
                "name": "A",
                "email": "a@e.com",
                "phone": "+880",
            },
            format="json",
        )
        .data["id"]
    )

    assert actors["user"].post(f"/api/admin/posts/{pid}/approve/").status_code == 403
    assert actors["staff"].post(f"/api/admin/posts/{pid}/approve/").status_code == 200
