"""Admin moderation use cases.

Note what is absent: any point logic. Points are derived from `Post.status` (LLD DEC-2), so
approving, hiding, and un-hiding move a single field and the leaderboard follows
automatically. There is no award, no reversal, and no cascade to keep in sync - which is
the entire reason the derived model was chosen over a ledger.
"""

import contextlib
from datetime import timedelta

from core.application.reports.dto import ModerateCommand
from core.domain.entities import Post, PostModerationLog
from core.domain.errors import ConflictError, PostNotFound
from core.domain.ids import UserId
from core.domain.pagination import Page, PageRequest
from core.domain.read_models import AuditLogEntry, PostAnalytics, PostFilter, StatusCounts
from core.domain.value_objects import ModerationAction, PostStatus, Severity
from core.ports.clock import Clock
from core.ports.notifications import Notifier
from core.ports.repositories import ModerationLogRepository, PostRepository, UserRepository
from core.ports.storage import ImageStorage
from core.ports.unit_of_work import UnitOfWork


class _ModerationUseCase:
    def __init__(
        self,
        posts: PostRepository,
        log: ModerationLogRepository,
        notifier: Notifier,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.posts = posts
        self.log = log
        self.notifier = notifier
        self.uow = uow
        self.clock = clock

    def _load(self, post_id) -> Post:
        post = self.posts.get(post_id)
        if post is None or post.deleted_at is not None:
            raise PostNotFound()
        return post

    def _record(self, cmd: ModerateCommand, action: ModerationAction) -> None:
        self.log.add(
            PostModerationLog(
                id=None,
                post_id=cmd.post_id,
                admin_id=cmd.admin_id,
                action=action,
                reason=cmd.reason,
                at=self.clock.now(),
            )
        )

    def _notify(self, send, *args) -> None:
        # A mail outage must not roll back a moderation decision that already committed.
        # No Celery, so this is best-effort and deliberately swallowed.
        with contextlib.suppress(Exception):
            send(*args)


class ApproveReport(_ModerationUseCase):
    def execute(self, cmd: ModerateCommand) -> Post:
        post = self._load(cmd.post_id)
        if post.status is PostStatus.APPROVED:
            raise ConflictError("This report is already approved.")

        with self.uow:
            post.approve(self.clock.now())
            updated = self.posts.update(post)
            self._record(cmd, ModerationAction.APPROVE)
            self.uow.commit()

        self._notify(self.notifier.send_post_approved, updated.reporter.email, updated)
        return updated


class RejectReport(_ModerationUseCase):
    def __init__(self, posts, log, notifier, uow, clock, images: ImageStorage) -> None:
        super().__init__(posts, log, notifier, uow, clock)
        self.images = images

    def execute(self, cmd: ModerateCommand) -> Post:
        post = self._load(cmd.post_id)

        with self.uow:
            post.reject(self.clock.now())  # soft delete - legacy code dropped the row
            updated = self.posts.update(post)
            self._record(cmd, ModerationAction.REJECT)
            self.uow.commit()

        # After commit: an image-delete failure must not undo the rejection.
        with contextlib.suppress(Exception):
            self.images.delete(post.image)
        self._notify(self.notifier.send_post_rejected, updated.reporter.email, updated, cmd.reason)
        return updated


class HideReport(_ModerationUseCase):
    def execute(self, cmd: ModerateCommand) -> Post:
        post = self._load(cmd.post_id)
        if post.status is not PostStatus.APPROVED:
            raise ConflictError("Only an approved report can be hidden.")

        with self.uow:
            post.hide()  # image retained, unlike reject
            updated = self.posts.update(post)
            self._record(cmd, ModerationAction.HIDE)
            self.uow.commit()
        return updated


class UnhideReport(_ModerationUseCase):
    def execute(self, cmd: ModerateCommand) -> Post:
        post = self._load(cmd.post_id)
        if post.status is not PostStatus.HIDDEN:
            raise ConflictError("This report is not hidden.")

        with self.uow:
            post.unhide(self.clock.now())  # approved_at is preserved, not reset
            updated = self.posts.update(post)
            self._record(cmd, ModerationAction.UNHIDE)
            self.uow.commit()
        return updated


class ListReportsForReview:
    """Admin listing - the only place a status filter is caller-supplied."""

    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(
        self,
        page: PageRequest,
        statuses: tuple[PostStatus, ...] = (PostStatus.PENDING,),
        severity: int | None = None,
        include_deleted: bool = False,
    ) -> Page[Post]:
        filter = PostFilter(
            statuses=statuses,
            severity=Severity(severity) if severity is not None else None,
            include_deleted=include_deleted,
        )
        return self.posts.list(filter, page)


class GetPostStats:
    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(self) -> StatusCounts:
        return self.posts.counts_by_status()


class GetPostAnalytics:
    """Dashboard time-series over a trailing window (default 8 weeks)."""

    def __init__(self, posts: PostRepository, clock: Clock, weeks: int = 8) -> None:
        self.posts = posts
        self.clock = clock
        self.weeks = weeks

    def execute(self) -> PostAnalytics:
        since = self.clock.now() - timedelta(weeks=self.weeks)
        return self.posts.analytics(since)


class ListAuditLog:
    """The moderation audit trail with each action's admin name resolved."""

    def __init__(self, log: ModerationLogRepository, users: UserRepository) -> None:
        self.log = log
        self.users = users

    def execute(self, page: PageRequest) -> Page[AuditLogEntry]:
        entries = self.log.list(page)
        names: dict[UserId, str] = {}

        def name_of(admin_id: UserId) -> str:
            if admin_id not in names:
                u = self.users.get(admin_id)
                names[admin_id] = u.full_name if u else "-"
            return names[admin_id]

        items = [
            AuditLogEntry(
                id=e.id,
                post_id=e.post_id,
                admin_name=name_of(e.admin_id),
                action=e.action,
                reason=e.reason,
                at=e.at,
            )
            for e in entries.items
        ]
        return Page(items=items, next_cursor=entries.next_cursor)
