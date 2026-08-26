"""Own-profile read and update."""

from core.application.accounts.avatars import upload_avatar
from core.application.accounts.dto import UpdateProfileCommand
from core.domain.entities import User
from core.domain.errors import UserNotFound
from core.domain.ids import UserId
from core.ports.repositories import UserRepository
from core.ports.storage import ImageStorage
from core.ports.unit_of_work import UnitOfWork


class GetProfile:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def execute(self, actor_id: UserId) -> User:
        user = self.users.get(actor_id)
        if user is None:
            raise UserNotFound()
        return user


class UpdateProfile:
    def __init__(
        self, users: UserRepository, uow: UnitOfWork, images: ImageStorage | None = None
    ) -> None:
        self.users = users
        self.uow = uow
        self.images = images

    def execute(self, cmd: UpdateProfileCommand, actor_id: UserId) -> User:
        user = self.users.get(actor_id)
        if user is None:
            raise UserNotFound()

        # Upload before the transaction: an external call inside the UoW would hold the row
        # lock across a slow network round-trip.
        new_avatar = upload_avatar(self.images, cmd.avatar)

        # Username, email, and role are deliberately not editable here: email changes need
        # re-verification and role changes are an admin action.
        with self.uow:
            if cmd.first_name is not None:
                user.first_name = cmd.first_name.strip()
            if cmd.last_name is not None:
                user.last_name = cmd.last_name.strip()
            if cmd.phone is not None:
                user.phone = cmd.phone.strip()
            if new_avatar is not None:
                user.avatar = new_avatar
            updated = self.users.update(user)
            self.uow.commit()
        return updated
