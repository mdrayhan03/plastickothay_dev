"""Dashboard analytics — weekly submitted/approved series and active-user count."""

from core.application.reports.moderation import GetPostAnalytics
from core.domain.value_objects import PostStatus


class TestGetPostAnalytics:
    def test_counts_submitted_approved_and_active_users(self, posts, clock, make_post, make_user):
        alice = make_user("alice")
        now = clock.now()
        make_post(reporter_id=alice.id, status=PostStatus.APPROVED, created=now, approved_at=now)
        make_post(status=PostStatus.PENDING, created=now)  # anonymous, not yet approved

        analytics = GetPostAnalytics(posts, clock).execute()
        assert sum(w.submitted for w in analytics.over_time) == 2
        assert sum(w.approved for w in analytics.over_time) == 1
        assert analytics.active_users == 1  # only the authenticated reporter counts

    def test_excludes_activity_before_the_window(self, posts, clock, make_post, make_user):
        alice = make_user("alice")
        long_ago = clock.now().replace(year=2025)
        make_post(
            reporter_id=alice.id, status=PostStatus.APPROVED, created=long_ago, approved_at=long_ago
        )

        analytics = GetPostAnalytics(posts, clock, weeks=8).execute()
        assert analytics.over_time == []
        assert analytics.active_users == 0

    def test_distinct_users(self, posts, clock, make_post, make_user):
        alice = make_user("alice")
        now = clock.now()
        make_post(reporter_id=alice.id, created=now, approved_at=now)
        make_post(reporter_id=alice.id, created=now, approved_at=now)  # same user twice
        analytics = GetPostAnalytics(posts, clock).execute()
        assert analytics.active_users == 1
