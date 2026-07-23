import pytest

from core.application.reports.dto import SubmitReportCommand
from core.application.reports.submission import SubmitReport
from core.domain.errors import ImageUploadFailed, InvalidLocation
from core.domain.value_objects import PostStatus


@pytest.fixture
def use_case(posts, users, images, uow, clock):
    return SubmitReport(posts, users, images, uow, clock)


def command(**overrides) -> SubmitReportCommand:
    defaults = dict(
        severity=3,
        lat=23.8103,
        lon=90.4125,
        photo_bytes=b"\xff\xd8\xff",
        filename="capture.jpg",
        content_type="image/jpeg",
        description="Plastic near the canal.",
        name="Walk-in Reporter",
        email="walkin@example.com",
        phone="+8801799999999",
    )
    return SubmitReportCommand(**{**defaults, **overrides})


class TestAnonymousSubmission:
    def test_uses_supplied_contact_details(self, use_case):
        post = use_case.execute(command(), actor_id=None)

        assert post.reporter_id is None
        assert post.is_anonymous
        assert post.reporter.name == "Walk-in Reporter"
        assert post.reporter.email == "walkin@example.com"

    def test_starts_pending_and_not_public(self, use_case):
        post = use_case.execute(command(), actor_id=None)

        assert post.status is PostStatus.PENDING
        assert not post.is_public  # nothing is public before a human approves it
        assert post.approved_at is None

    def test_uploads_the_photo(self, use_case, images):
        post = use_case.execute(command(), actor_id=None)
        assert images.uploaded[post.image.external_id] == b"\xff\xd8\xff"


class TestAuthenticatedSubmission:
    def test_ignores_client_supplied_contact_details(self, use_case, make_user):
        """Trust the token, not the body.

        Otherwise a logged-in user could attach a stranger's email and phone to a report.
        """
        alice = make_user("alice")

        post = use_case.execute(
            command(name="Someone Else", email="victim@example.com", phone="+880000"),
            actor_id=alice.id,
        )

        assert post.reporter_id == alice.id
        assert post.reporter.email == "alice@example.com"  # not victim@
        assert post.reporter.name == "Alice Tester"
        assert post.reporter.phone == "+8801700000000"

    def test_same_payload_shape_as_anonymous(self, use_case, make_user):
        alice = make_user("alice")
        anon = use_case.execute(command(), actor_id=None)
        auth = use_case.execute(command(), actor_id=alice.id)

        assert anon.status is auth.status
        assert auth.reporter_id == alice.id and anon.reporter_id is None


class TestValidation:
    def test_rejects_out_of_range_coordinates(self, use_case):
        with pytest.raises(InvalidLocation):
            use_case.execute(command(lat=91.0), actor_id=None)

    def test_rejects_invalid_severity(self, use_case):
        with pytest.raises(ValueError):
            use_case.execute(command(severity=9), actor_id=None)

    def test_blank_description_gets_a_default(self, use_case):
        post = use_case.execute(command(description="   "), actor_id=None)
        assert post.description == "No description provided."

    def test_filename_is_randomised(self, use_case):
        first = use_case.execute(command(), actor_id=None)
        second = use_case.execute(command(), actor_id=None)
        assert first.image.external_id != second.image.external_id


class TestFailureHandling:
    def test_upload_failure_creates_no_post(self, posts, users, uow, clock, images):
        images.fail_upload = True
        use_case = SubmitReport(posts, users, images, uow, clock)

        with pytest.raises(ImageUploadFailed):
            use_case.execute(command(), actor_id=None)

        assert posts.rows == {}
        assert not uow.committed

    def test_insert_failure_deletes_the_orphaned_upload(
        self, posts, users, images, uow, clock, monkeypatch
    ):
        """The upload is not transactional, so a failed insert would otherwise leave the
        file in Drive forever."""
        use_case = SubmitReport(posts, users, images, uow, clock)

        def boom(_post):
            raise RuntimeError("database is down")

        monkeypatch.setattr(posts, "add", boom)

        with pytest.raises(RuntimeError):
            use_case.execute(command(), actor_id=None)

        assert images.deleted == ["fake-1"]
        assert images.uploaded == {}
