"""Admin user management use cases — list, activate/deactivate, role change."""

import pytest

from core.application.accounts.administration import (
    DeleteUser,
    GetUserDetail,
    ListUsers,
    SetUserActive,
    SetUserRole,
)
from core.domain.errors import ConflictError, NotAuthorized, UserNotFound
from core.domain.pagination import PageRequest
from core.domain.value_objects import Role


@pytest.fixture
def list_users(users):
    return ListUsers(users)


@pytest.fixture
def set_active(users, uow):
    return SetUserActive(users, uow)


@pytest.fixture
def set_role(users, uow):
    return SetUserRole(users, uow)


@pytest.fixture
def delete_user(users, uow):
    return DeleteUser(users, uow)


class TestListUsers:
    def test_returns_all_users(self, list_users, make_user):
        make_user("alice")
        make_user("bob")
        page = list_users.execute(PageRequest(limit=10, cursor=None))
        assert {u.username for u in page.items} == {"alice", "bob"}

    def test_paginates(self, list_users, make_user):
        for i in range(3):
            make_user(f"u{i}")
        first = list_users.execute(PageRequest(limit=2, cursor=None))
        assert len(first.items) == 2
        assert first.next_cursor is not None
        second = list_users.execute(PageRequest(limit=2, cursor=first.next_cursor))
        assert len(second.items) == 1


class TestSetUserActive:
    def test_staff_can_deactivate_a_user(self, set_active, make_user):
        staff = make_user("mod", role=Role.STAFF)
        target = make_user("alice")
        updated = set_active.execute(target.id, False, staff.id)
        assert updated.is_active is False

    def test_cannot_deactivate_self(self, set_active, make_user):
        staff = make_user("mod", role=Role.STAFF)
        with pytest.raises(NotAuthorized):
            set_active.execute(staff.id, False, staff.id)

    def test_staff_cannot_deactivate_an_admin(self, set_active, make_user):
        staff = make_user("mod", role=Role.STAFF)
        admin = make_user("boss", role=Role.ADMIN)
        with pytest.raises(NotAuthorized):
            set_active.execute(admin.id, False, staff.id)

    def test_admin_can_deactivate_an_admin(self, set_active, make_user):
        admin1 = make_user("boss", role=Role.ADMIN)
        admin2 = make_user("boss2", role=Role.ADMIN)
        updated = set_active.execute(admin2.id, False, admin1.id)
        assert updated.is_active is False

    def test_regular_user_cannot(self, set_active, make_user):
        actor = make_user("alice")
        target = make_user("bob")
        with pytest.raises(NotAuthorized):
            set_active.execute(target.id, False, actor.id)

    def test_unknown_target(self, set_active, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        with pytest.raises(UserNotFound):
            set_active.execute(9999, False, admin.id)


class TestSetUserRole:
    def test_admin_can_promote(self, set_role, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        target = make_user("alice")
        updated = set_role.execute(target.id, Role.STAFF, admin.id)
        assert updated.role is Role.STAFF

    def test_staff_cannot_change_roles(self, set_role, make_user):
        staff = make_user("mod", role=Role.STAFF)
        target = make_user("alice")
        with pytest.raises(NotAuthorized):
            set_role.execute(target.id, Role.STAFF, staff.id)

    def test_cannot_change_own_role(self, set_role, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        with pytest.raises(NotAuthorized):
            set_role.execute(admin.id, Role.USER, admin.id)

    def test_unknown_target(self, set_role, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        with pytest.raises(UserNotFound):
            set_role.execute(9999, Role.STAFF, admin.id)


class TestGetUserDetail:
    def test_returns_user_and_contribution(
        self, users, leaderboard, point_rules, level_rules, make_user
    ):
        alice = make_user("alice")
        detail = GetUserDetail(users, leaderboard, point_rules, level_rules)
        user, contribution = detail.execute(alice.id)
        assert user.username == "alice"
        assert contribution.user_id == alice.id
        assert contribution.posts_approved == 0

    def test_unknown_user(self, users, leaderboard, point_rules, level_rules):
        detail = GetUserDetail(users, leaderboard, point_rules, level_rules)
        with pytest.raises(UserNotFound):
            detail.execute(9999)


class TestDeleteUser:
    def test_admin_deletes_an_inactive_user(self, delete_user, users, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        target = make_user("alice", is_active=False)
        delete_user.execute(target.id, admin.id)
        assert users.get(target.id) is None

    def test_refuses_an_active_user(self, delete_user, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        target = make_user("alice", is_active=True)
        with pytest.raises(ConflictError):
            delete_user.execute(target.id, admin.id)

    def test_refuses_self(self, delete_user, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        with pytest.raises(NotAuthorized):
            delete_user.execute(admin.id, admin.id)

    def test_refuses_deleting_an_admin(self, delete_user, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        other = make_user("boss2", role=Role.ADMIN, is_active=False)
        with pytest.raises(NotAuthorized):
            delete_user.execute(other.id, admin.id)

    def test_staff_cannot_delete(self, delete_user, make_user):
        staff = make_user("mod", role=Role.STAFF)
        target = make_user("alice", is_active=False)
        with pytest.raises(NotAuthorized):
            delete_user.execute(target.id, staff.id)

    def test_unknown_target(self, delete_user, make_user):
        admin = make_user("boss", role=Role.ADMIN)
        with pytest.raises(UserNotFound):
            delete_user.execute(9999, admin.id)
