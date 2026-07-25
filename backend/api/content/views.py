"""Content API — contact page, contact messages, feedback.

Public: read the contact page, submit a message, submit feedback (all AllowAny, throttled).
Admin: edit the contact page, list messages + update status, list feedback.
"""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.authentication import actor_id
from api.content.serializers import (
    ContactMessageSerializer,
    ContactPageSerializer,
    FeedbackSerializer,
    SiteConfigSerializer,
    SubmitContactMessageSerializer,
    SubmitFeedbackSerializer,
    UpdateContactPageSerializer,
    UpdateMessageStatusSerializer,
    UpdateSiteConfigSerializer,
)
from api.pagination import page_request, paginated_response
from api.permissions import IsAdmin, IsStaffOrAdmin
from config import container
from core.application.content.contact_page import (
    GetContactPage,
    UpdateContactPage,
    UpdateContactPageCommand,
)
from core.application.content.site_config import (
    GetSiteConfig,
    UpdateSiteConfig,
    UpdateSiteConfigCommand,
)
from core.application.engagement.submissions import (
    ListContactMessages,
    ListFeedback,
    SubmitContactMessage,
    SubmitContactMessageCommand,
    SubmitFeedback,
    SubmitFeedbackCommand,
)
from core.domain.value_objects import SocialLink


class ContactPageView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsStaffOrAdmin()]

    def get(self, request):
        page = GetContactPage(container.contact()).execute()
        return Response(ContactPageSerializer(page).data)

    def put(self, request):
        s = UpdateContactPageSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        cmd = UpdateContactPageCommand(
            heading=d["heading"],
            intro=d["intro"],
            email=d["email"],
            phone=d["phone"],
            address=d["address"],
            map_lat=d.get("map_lat"),
            map_lon=d.get("map_lon"),
            socials=tuple(SocialLink(**link) for link in d["socials"]),
        )
        page = UpdateContactPage(
            container.contact(), container.unit_of_work(), container.clock()
        ).execute(cmd, actor_id(request))
        return Response(ContactPageSerializer(page).data)


class ContactMessageView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "POST" else [IsStaffOrAdmin()]

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_scope = "contact_submit"
            return [ScopedRateThrottle()]
        return []

    def post(self, request):
        s = SubmitContactMessageSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        SubmitContactMessage(
            container.contact(), container.users(), container.unit_of_work(), container.clock()
        ).execute(SubmitContactMessageCommand(**s.validated_data), actor_id(request))
        return Response({"detail": "Message sent."}, status=201)

    def get(self, request):
        page = ListContactMessages(container.contact()).execute(page_request(request))
        return paginated_response(page, ContactMessageSerializer)


class FeedbackView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == "POST" else [IsStaffOrAdmin()]

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_scope = "feedback_submit"
            return [ScopedRateThrottle()]
        return []

    def post(self, request):
        s = SubmitFeedbackSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        SubmitFeedback(
            container.feedback(), container.users(), container.unit_of_work(), container.clock()
        ).execute(SubmitFeedbackCommand(**s.validated_data), actor_id(request))
        return Response({"detail": "Thanks for your feedback."}, status=201)

    def get(self, request):
        page = ListFeedback(container.feedback()).execute(page_request(request))
        return paginated_response(page, FeedbackSerializer)


class SiteConfigView(APIView):
    def get_permissions(self):
        # Read is public; editing site settings is admin-only (staff moderate, admins govern).
        return [AllowAny()] if self.request.method == "GET" else [IsAdmin()]

    def get(self, request):
        cfg = GetSiteConfig(container.site_config()).execute()
        return Response(SiteConfigSerializer(cfg).data)

    def put(self, request):
        s = UpdateSiteConfigSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        cfg = UpdateSiteConfig(
            container.site_config(), container.unit_of_work(), container.clock()
        ).execute(
            UpdateSiteConfigCommand(
                week_start=d["week_start"],
                site_name=d["site_name"],
                tagline=d["tagline"],
                map_lat=d.get("map_lat"),
                map_lon=d.get("map_lon"),
                map_zoom=d["map_zoom"],
                flags=d["flags"],
            ),
            actor_id(request),
        )
        return Response(SiteConfigSerializer(cfg).data)


class ContactMessageStatusView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def patch(self, request, message_id: int):
        s = UpdateMessageStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        repo = container.contact()
        msg = repo.get_message(message_id)
        if msg is None:
            from core.domain.errors import NotFoundError

            raise NotFoundError("Message not found.")
        msg.status = s.validated_data["status"]
        updated = repo.update_message(msg)
        return Response(ContactMessageSerializer(updated).data)
