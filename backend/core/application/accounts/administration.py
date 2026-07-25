"""Admin user management."""

from core.domain.entities import User
from core.domain.errors import ConflictError, NotAuthorized, UserNotFound
from core.domain.ids import UserId
from core.domain.pagination import Page, PageRequest
from core.domain.read_models import Contribution
from core.domain.value_objects import Role
from core.ports.repositories import (
    LeaderboardRepository,
    LevelRuleRepository,
    PointRuleRepository,
    UserRepository,
)
from core.ports.unit_of_work import UnitOfWork


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def execute(self, page: PageRequest) -> Page[User]:
        return self.users.list(page)


class GetUserDetail:
    """A single user plus their all-time contribution stats, for the admin profile drawer."""

    def __init__(
        self,
        users: UserRepository,
        leaderboard: LeaderboardRepository,
        point_rules: PointRuleRepository,
        level_rules: LevelRuleRepository,
    ) -> None:
        self.users = users
        self.leaderboard = leaderboard
        self.point_rules = point_rules
        self.level_rules = level_rules

    def execute(self, user_id: UserId) -> tuple[User, Contribution]:
        user = self.users.get(user_id)
        if user is None:
            raise UserNotFound()
        contribution = self.leaderboard.contribution_for(
            user_id, self.point_rules.active_rules(), self.level_rules.all()
        )
        return user, contribution


class SetUserRole:
    """Superuser only — enforced again at the HTTP layer by permission class."""

    def __init__(self, users: UserRepository, uow: UnitOfWork) -> None:
        self.users = users
        self.uow = uow

    def execute(self, target_id: UserId, role: Role, actor_id: UserId) -> User:
        actor = self.users.get(actor_id)
        if actor is None or actor.role is not Role.ADMIN:
            raise NotAuthorized("Only an admin can change roles.")
        target = self.users.get(target_id)
        if target is None:
            raise UserNotFound()
        if target_id == actor_id:
            # Without this, the last admin can demote themselves and lock everyone out.
            raise NotAuthorized("You cannot change your own role.")

        with self.uow:
            updated = self.users.set_role(target_id, role)
            self.uow.commit()
        return updated


class SetUserActive:
    def __init__(self, users: UserRepository, uow: UnitOfWork) -> None:
        self.users = users
        self.uow = uow

    def execute(self, target_id: UserId, is_active: bool, actor_id: UserId) -> User:
        actor = self.users.get(actor_id)
        if actor is None or not actor.role.is_moderator:
            raise NotAuthorized()
        target = self.users.get(target_id)
        if target is None:
            raise UserNotFound()
        if target_id == actor_id:
            raise NotAuthorized("You cannot deactivate yourself.")
        if target.role is Role.ADMIN and actor.role is not Role.ADMIN:
            raise NotAuthorized("Staff cannot deactivate an admin.")

        with self.uow:
            updated = self.users.set_active(target_id, is_active)
            self.uow.commit()
        return updated


class DeleteUser:
    """Admin only, and only for an already-deactivated account — a deliberate two-step so
    an active member can't be deleted in one click."""

    def __init__(self, users: UserRepository, uow: UnitOfWork) -> None:
        self.users = users
        self.uow = uow

    def execute(self, target_id: UserId, actor_id: UserId) -> None:
        actor = self.users.get(actor_id)
        if actor is None or actor.role is not Role.ADMIN:
            raise NotAuthorized("Only an admin can delete users.")
        target = self.users.get(target_id)
        if target is None:
            raise UserNotFound()
        if target_id == actor_id:
            raise NotAuthorized("You cannot delete yourself.")
        if target.role is Role.ADMIN:
            raise NotAuthorized("Admins cannot be deleted.")
        if target.is_active:
            raise ConflictError("Deactivate the user before deleting.")

        with self.uow:
            self.users.delete(target_id)
            self.uow.commit()
