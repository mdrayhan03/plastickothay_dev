import pytest

from core.application.reports.dto import ModerateCommand
from core.application.reports.moderation import (
    ApproveReport,
    HideReport,
    RejectReport,
    UnhideReport,
)
from core.application.scoring.leaderboard import GetContribution
from core.domain.errors import ConflictError, PostNotFound
from core.domain.value_objects import ModerationAction, PostStatus


@pytest.fixture
def deps(posts, moderation_log, notifier, uow, clock):
    return dict(posts=posts, log=moderation_log, notifier=notifier, uow=uow, clock=clock)


@pytest.fixture
def approve(deps):
    return ApproveReport(**deps)


@pytest.fixture
def reject(deps, images):
    return RejectReport(**deps, images=images)


@pytest.fixture
def hide(deps):
    return HideReport(**deps)


@pytest.fixture
def unhide(deps):
    return UnhideReport(**deps)


@pytest.fixture
def admin(make_user):
    from core.domain.value_objects import Role

    return make_user("admin", role=Role.ADMIN)


class TestApprove:
    def test_makes_the_post_public(self, approve, make_post, make_user, admin):
        alice = make_user("alice")
        post = make_post(reporter_id=alice.id, status=PostStatus.PENDING)

        updated = approve.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

        assert updated.status is PostStatus.APPROVED
        assert updated.is_public
        assert updated.approved_at is not None

    def test_emails_the_reporter(self, approve, make_post, admin, notifier):
        post = make_post(status=PostStatus.PENDING)
        approve.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

        assert len(notifier.approvals) == 1
        assert notifier.approvals[0][0] == post.reporter.email

    def test_writes_an_audit_entry(self, approve, make_post, admin, moderation_log):
        post = make_post(status=PostStatus.PENDING)
        approve.execute(ModerateCommand(post_id=post.id, admin_id=admin.id, reason="looks real"))

        entry = moderation_log.list_for_post(post.id)[0]
        assert entry.action is ModerationAction.APPROVE
        assert entry.admin_id == admin.id
        assert entry.reason == "looks real"

    def test_double_approve_is_refused(self, approve, make_post, admin):
        post = make_post(status=PostStatus.APPROVED)
        with pytest.raises(ConflictError):
            approve.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

    def test_mail_failure_does_not_undo_approval(self, approve, make_post, admin, notifier):
        post = make_post(status=PostStatus.PENDING)

        def boom(*_args):
            raise RuntimeError("mailjet is down")

        notifier.send_post_approved = boom

        updated = approve.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))
        assert updated.status is PostStatus.APPROVED  # committed regardless


class TestReject:
    def test_soft_deletes_and_removes_the_image(self, reject, make_post, admin, images):
        post = make_post(status=PostStatus.PENDING)
        external_id = post.image.external_id

        updated = reject.execute(ModerateCommand(post_id=post.id, admin_id=admin.id, reason="spam"))

        assert updated.status is PostStatus.REJECTED
        assert updated.deleted_at is not None  # legacy code dropped the row entirely
        assert external_id in images.deleted

    def test_rejected_post_cannot_be_moderated_again(self, reject, make_post, admin):
        post = make_post(status=PostStatus.PENDING)
        reject.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

        with pytest.raises(PostNotFound):
            reject.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))


class TestHideUnhide:
    def test_hide_keeps_the_image(self, hide, make_post, admin, images):
        post = make_post(status=PostStatus.APPROVED)
        updated = hide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

        assert updated.status is PostStatus.HIDDEN
        assert not updated.is_public
        assert images.deleted == []  # unlike reject

    def test_only_approved_posts_can_be_hidden(self, hide, make_post, admin):
        post = make_post(status=PostStatus.PENDING)
        with pytest.raises(ConflictError):
            hide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

    def test_unhide_preserves_the_original_approval_date(
        self, hide, unhide, make_post, admin, clock
    ):
        """approved_at must not shift, or un-hiding would move the post into a later
        leaderboard week (DEC-3)."""
        post = make_post(status=PostStatus.APPROVED)
        original = post.approved_at

        hide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))
        clock.advance(days=30)
        updated = unhide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))

        assert updated.status is PostStatus.APPROVED
        assert updated.approved_at == original

    def test_unhide_requires_hidden(self, unhide, make_post, admin):
        post = make_post(status=PostStatus.APPROVED)
        with pytest.raises(ConflictError):
            unhide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))


class TestModerationMovesPointsWithNoPointCode:
    """End-to-end proof of DEC-2: none of the moderation use cases touch points, yet the
    score follows the status."""

    def test_hide_then_unhide_round_trips_the_score(
        self,
        hide,
        unhide,
        make_post,
        make_user,
        admin,
        leaderboard,
        point_rules,
        level_rules,
        engagements,
        clock,
    ):
        from core.application.engagement.likes import LikePost
        from tests.fakes.system import FakeUnitOfWork

        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id, status=PostStatus.APPROVED)
        LikePost(hide.posts, engagements, FakeUnitOfWork(), clock).execute(post.id, bob.id)

        contribution = GetContribution(leaderboard, point_rules, level_rules)
        assert contribution.execute(alice.id).total_points == 103

        hide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))
        assert contribution.execute(alice.id).total_points == 0
        assert contribution.execute(bob.id).total_points == 0  # the like's points too

        unhide.execute(ModerateCommand(post_id=post.id, admin_id=admin.id))
        assert contribution.execute(alice.id).total_points == 103
        assert contribution.execute(bob.id).total_points == 1
