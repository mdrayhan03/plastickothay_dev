"""Like / unlike.

Anonymous callers may like (recorded, counted, displayed) but the like awards nothing to
anyone - including the post owner (LLD DEC-1). That is a security control: an anonymous
liker has no stable identity, so no unique constraint can bind them, and awarding the owner
3 points per anonymous like would let a five-line script print unlimited points with no
account. Enforced in core.domain.points.engagement_earns_points.
"""

from dataclasses import dataclass

from core.domain.entities import Engagement
from core.domain.errors import NotLiked, PostNotFound, SelfLikeNotAllowed
from core.domain.ids import PostId, UserId
from core.domain.value_objects import EngagementType
from core.ports.clock import Clock
from core.ports.repositories import EngagementRepository, PostRepository
from core.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class LikeResult:
    post_id: PostId
    likes: int
    liked_by_me: bool


class LikePost:
    def __init__(
        self,
        posts: PostRepository,
        engagements: EngagementRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self.posts = posts
        self.engagements = engagements
        self.uow = uow
        self.clock = clock

    def execute(self, post_id: PostId, actor_id: UserId | None) -> LikeResult:
        post = self.posts.get(post_id)
        if post is None or not post.is_public:
            raise PostNotFound()  # non-public posts are not likeable
        if actor_id is not None and actor_id == post.reporter_id:
            raise SelfLikeNotAllowed()

        with self.uow:
            # No check-then-act: uniqueness is the DB constraint's job, and a read-first
            # guard would let concurrent double-likes through (LLD §7.2). The repository
            # translates the constraint violation into AlreadyLiked.
            self.engagements.add(
                Engagement(
                    id=None,
                    post_id=post_id,
                    type=EngagementType.LIKE,
                    actor_id=actor_id,
                    created=self.clock.now(),
                )
            )
            self.uow.commit()

        return LikeResult(
            post_id=post_id,
            likes=self.engagements.count(post_id, EngagementType.LIKE),
            liked_by_me=actor_id is not None,
        )


class UnlikePost:
    def __init__(
        self,
        posts: PostRepository,
        engagements: EngagementRepository,
        uow: UnitOfWork,
    ) -> None:
        self.posts = posts
        self.engagements = engagements
        self.uow = uow

    def execute(self, post_id: PostId, actor_id: UserId) -> LikeResult:
        post = self.posts.get(post_id)
        if post is None or not post.is_public:
            raise PostNotFound()

        with self.uow:
            removed = self.engagements.remove_like(post_id, actor_id)
            if not removed:
                raise NotLiked()
            self.uow.commit()

        return LikeResult(
            post_id=post_id,
            likes=self.engagements.count(post_id, EngagementType.LIKE),
            liked_by_me=False,
        )
