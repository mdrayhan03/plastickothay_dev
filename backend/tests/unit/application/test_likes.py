import pytest

from core.application.engagement.likes import LikePost, UnlikePost
from core.domain.errors import AlreadyLiked, NotLiked, PostNotFound, SelfLikeNotAllowed
from core.domain.value_objects import EngagementType, PostStatus


@pytest.fixture
def like(posts, engagements, uow, clock):
    return LikePost(posts, engagements, uow, clock)


@pytest.fixture
def unlike(posts, engagements, uow):
    return UnlikePost(posts, engagements, uow)


class TestLiking:
    def test_authenticated_user_can_like_someone_elses_post(self, like, make_user, make_post):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)

        result = like.execute(post.id, actor_id=bob.id)

        assert result.likes == 1
        assert result.liked_by_me is True

    def test_anonymous_user_can_like(self, like, make_user, make_post):
        """DEC-1: recorded and counted — it just pays nobody (see test_points)."""
        alice = make_user("alice")
        post = make_post(reporter_id=alice.id)

        result = like.execute(post.id, actor_id=None)

        assert result.likes == 1
        assert result.liked_by_me is False

    def test_one_like_per_user_per_post(self, like, make_user, make_post):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)
        like.execute(post.id, actor_id=bob.id)

        with pytest.raises(AlreadyLiked):
            like.execute(post.id, actor_id=bob.id)

        assert like.engagements.count(post.id, EngagementType.LIKE) == 1

    def test_self_like_is_refused(self, like, make_user, make_post):
        alice = make_user("alice")
        post = make_post(reporter_id=alice.id)

        with pytest.raises(SelfLikeNotAllowed):
            like.execute(post.id, actor_id=alice.id)

    def test_anonymous_likes_are_not_deduplicated(self, like, make_user, make_post):
        """Anonymous callers have no stable identity, so nothing can bind them.

        This is precisely why DEC-1 makes them worth zero points — the constraint that
        stops abuse for authenticated users cannot exist here.
        """
        alice = make_user("alice")
        post = make_post(reporter_id=alice.id)

        like.execute(post.id, actor_id=None)
        like.execute(post.id, actor_id=None)

        assert like.engagements.count(post.id, EngagementType.LIKE) == 2

    @pytest.mark.parametrize("status", [PostStatus.PENDING, PostStatus.HIDDEN])
    def test_non_public_posts_are_not_likeable(self, like, make_user, make_post, status):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id, status=status)

        with pytest.raises(PostNotFound):
            like.execute(post.id, actor_id=bob.id)

    def test_missing_post(self, like, make_user):
        bob = make_user("bob")
        with pytest.raises(PostNotFound):
            like.execute(9999, actor_id=bob.id)

    def test_anonymous_post_can_be_liked(self, like, make_user, make_post):
        bob = make_user("bob")
        post = make_post(reporter_id=None)  # nobody to pay, but likeable

        assert like.execute(post.id, actor_id=bob.id).likes == 1


class TestUnliking:
    def test_removes_the_like(self, like, unlike, make_user, make_post):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)
        like.execute(post.id, actor_id=bob.id)

        result = unlike.execute(post.id, actor_id=bob.id)

        assert result.likes == 0
        assert result.liked_by_me is False

    def test_unliking_without_a_like_is_an_error(self, unlike, make_user, make_post):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)

        with pytest.raises(NotLiked):
            unlike.execute(post.id, actor_id=bob.id)

    def test_relike_after_unlike_is_allowed(self, like, unlike, make_user, make_post):
        alice, bob = make_user("alice"), make_user("bob")
        post = make_post(reporter_id=alice.id)
        like.execute(post.id, actor_id=bob.id)
        unlike.execute(post.id, actor_id=bob.id)

        assert like.execute(post.id, actor_id=bob.id).likes == 1
