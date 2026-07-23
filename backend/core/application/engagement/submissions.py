"""Feedback ("rate us") and contact messages.

Both are greenfield: the legacy `feedback()` view only rendered a template and never handled
POST, and the `Rate` document had no fields at all. Both accept anonymous submissions.
"""

from dataclasses import dataclass

from core.domain.entities import ContactMessage, Feedback
from core.domain.errors import InvalidRating, UserNotFound
from core.domain.ids import UserId
from core.domain.pagination import Page, PageRequest
from core.ports.clock import Clock
from core.ports.repositories import ContactRepository, FeedbackRepository, UserRepository
from core.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class SubmitFeedbackCommand:
    rating: int
    comment: str = ""
    name: str = ""
    email: str = ""


@dataclass(frozen=True, slots=True)
class SubmitContactMessageCommand:
    subject: str
    message: str
    name: str = ""
    email: str = ""
    phone: str = ""


class SubmitFeedback:
    def __init__(
        self,
        feedback: FeedbackRepository,
        users: UserRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.feedback = feedback
        self.users = users
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: SubmitFeedbackCommand, actor_id: UserId | None) -> Feedback:
        if not 1 <= cmd.rating <= 5:
            raise InvalidRating(rating=cmd.rating)

        name, email = self._identify(cmd.name, cmd.email, actor_id)
        with self.uow:
            saved = self.feedback.add(
                Feedback(
                    id=None,
                    user_id=actor_id,
                    name=name,
                    email=email,
                    rating=cmd.rating,
                    comment=cmd.comment.strip(),
                    created=self.clock.now(),
                )
            )
            self.uow.commit()
        return saved

    def _identify(self, name: str, email: str, actor_id: UserId | None) -> tuple[str, str]:
        if actor_id is None:
            return name.strip(), email.strip()
        user = self.users.get(actor_id)
        if user is None:
            raise UserNotFound()
        return user.full_name, user.email


class SubmitContactMessage:
    def __init__(
        self,
        contact: ContactRepository,
        users: UserRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.contact = contact
        self.users = users
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: SubmitContactMessageCommand, actor_id: UserId | None) -> ContactMessage:
        name, email, phone = cmd.name.strip(), cmd.email.strip(), cmd.phone.strip()
        if actor_id is not None:
            user = self.users.get(actor_id)
            if user is None:
                raise UserNotFound()
            name, email, phone = user.full_name, user.email, user.phone

        with self.uow:
            saved = self.contact.add_message(
                ContactMessage(
                    id=None,
                    user_id=actor_id,
                    name=name,
                    email=email,
                    phone=phone,
                    subject=cmd.subject.strip(),
                    message=cmd.message.strip(),
                    status="new",
                    created=self.clock.now(),
                )
            )
            self.uow.commit()
        return saved


class ListFeedback:
    def __init__(self, feedback: FeedbackRepository) -> None:
        self.feedback = feedback

    def execute(self, page: PageRequest) -> Page[Feedback]:
        return self.feedback.list(page)


class ListContactMessages:
    def __init__(self, contact: ContactRepository) -> None:
        self.contact = contact

    def execute(self, page: PageRequest) -> Page[ContactMessage]:
        return self.contact.list_messages(page)
