"""Audit log listing — resolves each moderation action's admin name."""

from core.application.reports.moderation import ListAuditLog
from core.domain.entities import PostModerationLog
from core.domain.ids import PostId
from core.domain.pagination import PageRequest
from core.domain.value_objects import ModerationAction, Role


def _log(moderation_log, admin_id, post_id, action, at):
    moderation_log.add(
        PostModerationLog(
            id=None, post_id=PostId(post_id), admin_id=admin_id, action=action, reason="", at=at
        )
    )


class TestListAuditLog:
    def test_resolves_admin_name_and_newest_first(self, moderation_log, users, make_user, clock):
        admin = make_user("boss", role=Role.ADMIN)
        _log(moderation_log, admin.id, 5, ModerationAction.APPROVE, clock.now())
        clock.advance(minutes=1)
        _log(moderation_log, admin.id, 6, ModerationAction.HIDE, clock.now())

        page = ListAuditLog(moderation_log, users).execute(PageRequest(limit=10, cursor=None))
        assert [e.post_id for e in page.items] == [6, 5]  # newest first
        assert page.items[0].admin_name == admin.full_name
        assert page.items[0].action is ModerationAction.HIDE

    def test_missing_admin_falls_back(self, moderation_log, users, clock):
        _log(moderation_log, 9999, 5, ModerationAction.REJECT, clock.now())
        page = ListAuditLog(moderation_log, users).execute(PageRequest(limit=10, cursor=None))
        assert page.items[0].admin_name == "—"
