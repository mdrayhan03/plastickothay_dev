"""Report submission — the one endpoint open to anonymous and authenticated callers alike."""

import contextlib
import uuid

from core.application.reports.dto import SubmitReportCommand
from core.domain.entities import Post
from core.domain.errors import UserNotFound
from core.domain.ids import UserId
from core.domain.value_objects import GeoPoint, PostStatus, Reporter, Severity
from core.ports.clock import Clock
from core.ports.repositories import PostRepository, UserRepository
from core.ports.storage import ImageStorage
from core.ports.unit_of_work import UnitOfWork


class SubmitReport:
    def __init__(
        self,
        posts: PostRepository,
        users: UserRepository,
        images: ImageStorage,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.posts = posts
        self.users = users
        self.images = images
        self.uow = uow
        self.clock = clock

    def execute(self, cmd: SubmitReportCommand, actor_id: UserId | None) -> Post:
        reporter = self._resolve_reporter(cmd, actor_id)
        severity = Severity(cmd.severity)
        location = GeoPoint(cmd.lat, cmd.lon)

        filename = self._filename(cmd)
        image = self.images.upload(cmd.photo_bytes, filename, cmd.content_type)

        try:
            with self.uow:
                post = Post(
                    id=None,
                    reporter=reporter,
                    reporter_id=actor_id,
                    severity=severity,
                    image=image,
                    location=location,
                    place_name=cmd.place_name.strip(),
                    description=cmd.description.strip() or "No description provided.",
                    status=PostStatus.PENDING,
                    created=self.clock.now(),
                )
                saved = self.posts.add(post)
                self.uow.commit()
        except Exception:
            # The upload is not part of the transaction, so a failed insert would otherwise
            # orphan the file in Drive forever. Compensate, then re-raise.
            self._discard(image)
            raise

        return saved

    def _resolve_reporter(self, cmd: SubmitReportCommand, actor_id: UserId | None) -> Reporter:
        if actor_id is None:
            return Reporter(name=cmd.name.strip(), email=cmd.email.strip(), phone=cmd.phone.strip())

        user = self.users.get(actor_id)
        if user is None:
            raise UserNotFound()
        # Authenticated: trust the token, not the body. Otherwise a logged-in user could
        # attach a stranger's email and phone to a report (LLD §7.1).
        return user.as_reporter()

    def _filename(self, cmd: SubmitReportCommand) -> str:
        suffix = cmd.filename.rsplit(".", 1)[-1] if "." in cmd.filename else "jpg"
        return f"{uuid.uuid4()}.{suffix}"

    def _discard(self, image) -> None:
        # Best-effort cleanup; never mask the original failure.
        with contextlib.suppress(Exception):
            self.images.delete(image)
