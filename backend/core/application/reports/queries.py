"""Report read use cases.

Public listing pins ``statuses`` to APPROVED HERE, in the use case — not in the view, and
never from a query parameter. The legacy `posts()` view defaulted to every post regardless
of status, which combined with a serializer exposing email and phone would have published
the contact details of everyone who ever filed a report (LLD §8.3).
"""

from core.application.reports.dto import UpdateDescriptionCommand
from core.domain.entities import Post
from core.domain.errors import NotAuthorized, PostNotFound
from core.domain.ids import PostId, UserId
from core.domain.pagination import Page, PageRequest
from core.domain.read_models import AdminMapMarker, MapMarker, PostFilter
from core.domain.value_objects import PostStatus, Severity
from core.ports.repositories import PostRepository
from core.ports.unit_of_work import UnitOfWork

PUBLIC_STATUSES = (PostStatus.APPROVED,)


class ListReports:
    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(
        self,
        page: PageRequest,
        severity: int | None = None,
        created_after=None,
        created_before=None,
    ) -> Page[Post]:
        filter = PostFilter(
            statuses=PUBLIC_STATUSES,
            severity=Severity(severity) if severity is not None else None,
            created_after=created_after,
            created_before=created_before,
        )
        return self.posts.list(filter, page)


class GetReport:
    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(self, post_id: PostId) -> Post:
        post = self.posts.get(post_id)
        if post is None or not post.is_public:
            # Deliberately PostNotFound, not NotAuthorized: a 403 on a pending post would
            # confirm it exists and leak the moderation queue.
            raise PostNotFound()
        return post


class ListMapMarkers:
    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(self) -> list[MapMarker]:
        return self.posts.list_map_markers()


class ListAdminMapMarkers:
    """All non-deleted reports (any status) for the admin density map."""

    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(self) -> list[AdminMapMarker]:
        return self.posts.list_admin_map_markers()


class ListOwnReports:
    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(self, actor_id: UserId, page: PageRequest) -> Page[Post]:
        filter = PostFilter(
            statuses=(PostStatus.APPROVED, PostStatus.PENDING, PostStatus.HIDDEN),
            reporter_id=actor_id,
        )
        return self.posts.list(filter, page)


class ListUserReports:
    """A user's public reports — approved only (never another user's pending/hidden)."""

    def __init__(self, posts: PostRepository) -> None:
        self.posts = posts

    def execute(self, user_id: UserId, page: PageRequest) -> Page[Post]:
        filter = PostFilter(statuses=PUBLIC_STATUSES, reporter_id=user_id)
        return self.posts.list(filter, page)


class UpdateReportDescription:
    def __init__(self, posts: PostRepository, uow: UnitOfWork) -> None:
        self.posts = posts
        self.uow = uow

    def execute(self, cmd: UpdateDescriptionCommand) -> Post:
        post = self.posts.get(cmd.post_id)
        if post is None or post.deleted_at is not None:
            raise PostNotFound()
        if post.reporter_id is None or post.reporter_id != cmd.actor_id:
            raise NotAuthorized("You can only edit your own report.")

        with self.uow:
            post.description = cmd.description.strip() or "No description provided."
            updated = self.posts.update(post)
            self.uow.commit()
        return updated
