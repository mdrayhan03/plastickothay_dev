"""In-memory repository fakes.

These exist so the use-case suite runs with no database (LLD §2.1 acceptance test). The
fake leaderboard delegates to core.domain.points — the same reference implementation the
contract suite checks the production SQL against.
"""

from __future__ import annotations  # `def list(...)` shadows the builtin in class bodies

from datetime import datetime

from core.domain.entities import (
    OTP,
    BadgeRule,
    ContactMessage,
    ContactPage,
    Engagement,
    Feedback,
    LevelRule,
    Post,
    PostModerationLog,
    SiteConfig,
    User,
    UserBadge,
)
from core.domain.errors import AlreadyLiked, EmailTaken, UsernameTaken, UserNotFound
from core.domain.ids import (
    ContactMessageId,
    EngagementId,
    FeedbackId,
    ModerationLogId,
    OTPId,
    PostId,
    UserId,
)
from core.domain.pagination import Page, PageRequest
from core.domain.points import (
    Rules,
    compute_breakdown,
    compute_scores,
    level_for,
    level_progress,
)
from core.domain.read_models import (
    Contribution,
    LeaderboardRow,
    MapMarker,
    PostFilter,
    StatusCounts,
)
from core.domain.value_objects import EngagementType, OTPPurpose, PostStatus, Role
from core.ports.repositories import (
    BadgeRepository,
    ContactRepository,
    EngagementRepository,
    FeedbackRepository,
    LeaderboardRepository,
    LevelRuleRepository,
    ModerationLogRepository,
    OTPRepository,
    PointRuleRepository,
    PostRepository,
    SiteConfigRepository,
    UserRepository,
)


def _paginate(items: list, page: PageRequest) -> Page:
    """Offset-encoded cursor. Production uses keyset over (created, id); the fake only
    needs the same *contract*, not the same mechanism."""
    start = int(page.cursor) if page.cursor else 0
    window = items[start : start + page.limit]
    next_cursor = str(start + page.limit) if start + page.limit < len(items) else None
    return Page(items=window, next_cursor=next_cursor)


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.rows: dict[UserId, User] = {}
        self.passwords: dict[UserId, str] = {}
        self._seq = 0

    def _next_id(self) -> UserId:
        self._seq += 1
        return UserId(self._seq)

    def get(self, id: UserId) -> User | None:
        return self.rows.get(id)

    def get_by_username(self, username: str) -> User | None:
        return next((u for u in self.rows.values() if u.username == username), None)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def add(self, user: User, password: str) -> User:
        if self.get_by_username(user.username):
            raise UsernameTaken()
        if self.get_by_email(user.email):
            raise EmailTaken()
        user.id = self._next_id()
        self.rows[user.id] = user
        self.passwords[user.id] = password
        return user

    def update(self, user: User) -> User:
        if user.id is None or user.id not in self.rows:
            raise UserNotFound()
        self.rows[user.id] = user
        return user

    def set_password(self, id: UserId, password: str) -> None:
        if id not in self.rows:
            raise UserNotFound()
        self.passwords[id] = password

    def verify_password(self, id: UserId, password: str) -> bool:
        return self.passwords.get(id) == password

    def set_role(self, id: UserId, role: Role) -> User:
        user = self.rows.get(id)
        if user is None:
            raise UserNotFound()
        user.role = role
        return user

    def set_active(self, id: UserId, is_active: bool) -> User:
        user = self.rows.get(id)
        if user is None:
            raise UserNotFound()
        user.is_active = is_active
        return user

    def touch_last_login(self, id: UserId, at: datetime) -> None:
        if id in self.rows:
            self.rows[id].last_login = at

    def list(self, page: PageRequest) -> Page[User]:
        ordered = sorted(self.rows.values(), key=lambda u: u.id or 0)
        return _paginate(ordered, page)


class InMemoryOTPRepository(OTPRepository):
    def __init__(self) -> None:
        self.rows: list[OTP] = []
        self._seq = 0

    def add(self, otp: OTP) -> OTP:
        self._seq += 1
        otp.id = OTPId(self._seq)
        self.rows.append(otp)
        return otp

    def latest_valid_for(self, username: str, purpose: OTPPurpose, now: datetime) -> OTP | None:
        candidates = [
            o
            for o in self.rows
            if o.username == username and o.purpose is purpose and not o.is_expired(now)
        ]
        return max(candidates, key=lambda o: o.created_at, default=None)

    def invalidate_for(self, username: str, purpose: OTPPurpose) -> None:
        self.rows = [r for r in self.rows if not (r.username == username and r.purpose is purpose)]

    def purge_expired(self, now: datetime) -> int:
        before = len(self.rows)
        self.rows = [r for r in self.rows if not r.is_expired(now)]
        return before - len(self.rows)


class InMemoryPostRepository(PostRepository):
    def __init__(self) -> None:
        self.rows: dict[PostId, Post] = {}
        self._seq = 0

    def get(self, id: PostId) -> Post | None:
        return self.rows.get(id)

    def add(self, post: Post) -> Post:
        self._seq += 1
        post.id = PostId(self._seq)
        self.rows[post.id] = post
        return post

    def update(self, post: Post) -> Post:
        assert post.id is not None
        self.rows[post.id] = post
        return post

    def list(self, filter: PostFilter, page: PageRequest) -> Page[Post]:
        rows = [p for p in self.rows.values() if self._matches(p, filter)]
        rows.sort(key=lambda p: (p.created or datetime.min, p.id or 0), reverse=True)
        return _paginate(rows, page)

    def _matches(self, post: Post, f: PostFilter) -> bool:
        if post.status not in f.statuses:
            return False
        if not f.include_deleted and post.deleted_at is not None:
            return False
        if f.severity is not None and post.severity is not f.severity:
            return False
        if f.reporter_id is not None and post.reporter_id != f.reporter_id:
            return False
        if f.created_after is not None and (post.created is None or post.created < f.created_after):
            return False
        return not (
            f.created_before is not None
            and (post.created is None or post.created > f.created_before)
        )

    def list_map_markers(self) -> list[MapMarker]:
        return [
            MapMarker(id=p.id, lat=p.location.lat, lon=p.location.lon, severity=p.severity)
            for p in self.rows.values()
            if p.is_public and p.id is not None
        ]

    def counts_by_status(self) -> StatusCounts:
        counts: dict[PostStatus, int] = {}
        for p in self.rows.values():
            if p.deleted_at is None or p.status is PostStatus.REJECTED:
                counts[p.status] = counts.get(p.status, 0) + 1
        return StatusCounts(counts=counts)


class InMemoryEngagementRepository(EngagementRepository):
    def __init__(self) -> None:
        self.rows: list[Engagement] = []
        self._seq = 0

    def add(self, engagement: Engagement) -> Engagement:
        # Mirrors the partial unique index: one like per user per post, but comments are
        # unconstrained. Anonymous rows are not constrained at all — nothing identifies
        # them, which is exactly why they award no points (DEC-1).
        if (
            engagement.type is EngagementType.LIKE
            and engagement.actor_id is not None
            and self.get_like(engagement.post_id, engagement.actor_id) is not None
        ):
            raise AlreadyLiked()
        self._seq += 1
        engagement.id = EngagementId(self._seq)
        self.rows.append(engagement)
        return engagement

    def get_like(self, post_id: PostId, actor_id: UserId) -> Engagement | None:
        return next(
            (
                e
                for e in self.rows
                if e.post_id == post_id
                and e.actor_id == actor_id
                and e.type is EngagementType.LIKE
            ),
            None,
        )

    def remove_like(self, post_id: PostId, actor_id: UserId) -> bool:
        existing = self.get_like(post_id, actor_id)
        if existing is None:
            return False
        self.rows.remove(existing)
        return True

    def count(self, post_id: PostId, type: EngagementType) -> int:
        return sum(1 for e in self.rows if e.post_id == post_id and e.type is type)

    def counts_for(self, post_ids: list[PostId], type: EngagementType) -> dict[PostId, int]:
        return {pid: self.count(pid, type) for pid in post_ids}

    def liked_post_ids(self, post_ids: list[PostId], actor_id: UserId) -> set[PostId]:
        return {
            e.post_id
            for e in self.rows
            if e.actor_id == actor_id and e.type is EngagementType.LIKE and e.post_id in post_ids
        }


class InMemoryPointRuleRepository(PointRuleRepository):
    def __init__(self, rules: Rules | None = None) -> None:
        from tests.fakes.seed import DEFAULT_POINT_RULES

        self.rules = dict(rules) if rules is not None else dict(DEFAULT_POINT_RULES)

    def active_rules(self) -> Rules:
        return dict(self.rules)


class InMemoryLevelRuleRepository(LevelRuleRepository):
    def __init__(self, levels: list[LevelRule] | None = None) -> None:
        from tests.fakes.seed import DEFAULT_LEVEL_RULES

        self.levels = levels if levels is not None else list(DEFAULT_LEVEL_RULES)

    def all(self) -> list[LevelRule]:
        return list(self.levels)


class InMemoryLeaderboardRepository(LeaderboardRepository):
    """Reference implementation of the calculation strategy.

    Delegates to core.domain.points. The production Postgres implementation must produce
    identical results for every scenario in tests/contract/.
    """

    def __init__(
        self,
        posts: InMemoryPostRepository,
        engagements: InMemoryEngagementRepository,
        users: InMemoryUserRepository,
        clock,
    ) -> None:
        self.posts = posts
        self.engagements = engagements
        self.users = users
        self.clock = clock

    def top(self, since, rules: Rules, page: PageRequest) -> Page[LeaderboardRow]:
        scores = compute_scores(self.posts.rows.values(), self.engagements.rows, rules, since)

        ranked = []
        for user_id, breakdown in scores.items():
            if breakdown.points <= 0:
                continue
            user = self.users.get(user_id)
            if user is None:
                continue
            ranked.append((user, breakdown.points))

        # Ties break on earliest date_joined, matching the SQL's ORDER BY.
        ranked.sort(key=lambda r: (-r[1], r[0].date_joined or datetime.min, r[0].id or 0))
        rows = [
            LeaderboardRow(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                points=points,
                rank=index + 1,
            )
            for index, (user, points) in enumerate(ranked)
        ]
        return _paginate(rows, page)

    def contribution_for(
        self,
        user_id: UserId,
        rules: Rules,
        levels: list[LevelRule],
    ) -> Contribution:
        breakdown = compute_breakdown(
            user_id, self.posts.rows.values(), self.engagements.rows, rules, since=None
        )
        current = level_for(breakdown.points, levels)
        to_next, progress = level_progress(breakdown.points, levels)
        return Contribution(
            user_id=user_id,
            total_points=breakdown.points,
            posts_approved=breakdown.posts_approved,
            likes_received=breakdown.likes_received,
            likes_given=breakdown.likes_given,
            level=current.level,
            level_title=current.title,
            points_to_next_level=to_next,
            progress_percentage=progress,
        )


class InMemoryFeedbackRepository(FeedbackRepository):
    def __init__(self) -> None:
        self.rows: list[Feedback] = []
        self._seq = 0

    def add(self, feedback: Feedback) -> Feedback:
        self._seq += 1
        feedback.id = FeedbackId(self._seq)
        self.rows.append(feedback)
        return feedback

    def list(self, page: PageRequest) -> Page[Feedback]:
        ordered = sorted(self.rows, key=lambda f: f.id or 0, reverse=True)
        return _paginate(ordered, page)


class InMemoryContactRepository(ContactRepository):
    def __init__(self) -> None:
        self.page = ContactPage()
        self.messages: list[ContactMessage] = []
        self._seq = 0

    def get_page(self) -> ContactPage:
        return self.page

    def save_page(self, page: ContactPage) -> ContactPage:
        self.page = page
        return page

    def add_message(self, message: ContactMessage) -> ContactMessage:
        self._seq += 1
        message.id = ContactMessageId(self._seq)
        self.messages.append(message)
        return message

    def get_message(self, id: ContactMessageId) -> ContactMessage | None:
        return next((m for m in self.messages if m.id == id), None)

    def update_message(self, message: ContactMessage) -> ContactMessage:
        for index, existing in enumerate(self.messages):
            if existing.id == message.id:
                self.messages[index] = message
        return message

    def list_messages(self, page: PageRequest) -> Page[ContactMessage]:
        ordered = sorted(self.messages, key=lambda m: m.id or 0, reverse=True)
        return _paginate(ordered, page)


class InMemoryModerationLogRepository(ModerationLogRepository):
    def __init__(self) -> None:
        self.rows: list[PostModerationLog] = []
        self._seq = 0

    def add(self, entry: PostModerationLog) -> PostModerationLog:
        self._seq += 1
        entry.id = ModerationLogId(self._seq)
        self.rows.append(entry)
        return entry

    def list_for_post(self, post_id: PostId) -> list[PostModerationLog]:
        return [r for r in self.rows if r.post_id == post_id]


class InMemorySiteConfigRepository(SiteConfigRepository):
    def __init__(self) -> None:
        self.config = SiteConfig()  # defaults

    def get(self) -> SiteConfig:
        return self.config

    def save(self, config: SiteConfig) -> SiteConfig:
        self.config = config
        return config


class InMemoryBadgeRepository(BadgeRepository):
    def __init__(self, rules: list[BadgeRule] | None = None) -> None:
        from tests.fakes.seed import DEFAULT_BADGE_RULES

        self.rules = rules if rules is not None else list(DEFAULT_BADGE_RULES)
        self.earned: list[UserBadge] = []

    def active_rules(self) -> list[BadgeRule]:
        return [r for r in self.rules if r.active]

    def rules_by_code(self) -> dict[str, BadgeRule]:
        return {r.code: r for r in self.rules}

    def earned_codes(self, user_id: UserId) -> set[str]:
        return {b.badge_code for b in self.earned if b.user_id == user_id}

    def award(self, user_id: UserId, code: str, at) -> None:
        if code not in self.earned_codes(user_id):  # idempotent
            self.earned.append(UserBadge(user_id=user_id, badge_code=code, earned_at=at))

    def list_earned(self, user_id: UserId) -> list[UserBadge]:
        return sorted(
            (b for b in self.earned if b.user_id == user_id), key=lambda b: b.earned_at
        )
