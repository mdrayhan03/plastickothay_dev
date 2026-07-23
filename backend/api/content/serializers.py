from rest_framework import serializers

from core.domain.entities import ContactMessage, ContactPage, Feedback, SiteConfig


class SocialLinkSerializer(serializers.Serializer):
    platform = serializers.CharField()
    url = serializers.URLField()
    order = serializers.IntegerField(default=0)


class ContactPageSerializer(serializers.Serializer):
    heading = serializers.CharField(allow_blank=True)
    intro = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    address = serializers.CharField(allow_blank=True)
    map_lat = serializers.SerializerMethodField()
    map_lon = serializers.SerializerMethodField()
    socials = serializers.SerializerMethodField()

    def get_map_lat(self, page: ContactPage):
        return page.map_point.lat if page.map_point else None

    def get_map_lon(self, page: ContactPage):
        return page.map_point.lon if page.map_point else None

    def get_socials(self, page: ContactPage):
        return [{"platform": s.platform, "url": s.url, "order": s.order} for s in page.socials]


class UpdateContactPageSerializer(serializers.Serializer):
    heading = serializers.CharField(allow_blank=True, default="")
    intro = serializers.CharField(allow_blank=True, default="")
    email = serializers.EmailField(allow_blank=True, default="")
    phone = serializers.CharField(allow_blank=True, default="")
    address = serializers.CharField(allow_blank=True, default="")
    map_lat = serializers.FloatField(required=False, allow_null=True)
    map_lon = serializers.FloatField(required=False, allow_null=True)
    socials = SocialLinkSerializer(many=True, required=False, default=list)


class SubmitContactMessageSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


class ContactMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    subject = serializers.CharField()
    message = serializers.CharField()
    status = serializers.CharField()
    created = serializers.DateTimeField()

    def to_representation(self, msg: ContactMessage):
        return {
            "id": msg.id, "name": msg.name, "email": msg.email, "phone": msg.phone,
            "subject": msg.subject, "message": msg.message, "status": msg.status,
            "created": msg.created,
        }


class UpdateMessageStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["new", "read", "replied"])


class SiteConfigSerializer(serializers.Serializer):
    """Public shape — the frontend fetches this on boot."""

    def to_representation(self, cfg: SiteConfig):
        from config import container

        logo_url = container.image_storage().public_url(cfg.logo) if cfg.logo else None
        return {
            "week_start": cfg.week_start.value,
            "site_name": cfg.site_name,
            "tagline": cfg.tagline,
            "logo_url": logo_url,
            "map_center": (
                {"lat": cfg.map_center.lat, "lon": cfg.map_center.lon}
                if cfg.map_center else None
            ),
            "map_zoom": cfg.map_zoom,
            "flags": cfg.flags,
        }


class UpdateSiteConfigSerializer(serializers.Serializer):
    week_start = serializers.ChoiceField(choices=["monday", "sunday"])
    site_name = serializers.CharField(max_length=255)
    tagline = serializers.CharField(max_length=512, allow_blank=True, default="")
    map_lat = serializers.FloatField(required=False, allow_null=True)
    map_lon = serializers.FloatField(required=False, allow_null=True)
    map_zoom = serializers.IntegerField(min_value=1, max_value=20, default=12)
    flags = serializers.DictField(child=serializers.BooleanField(), required=False, default=dict)


class SubmitFeedbackSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")


class FeedbackSerializer(serializers.Serializer):
    def to_representation(self, fb: Feedback):
        return {
            "id": fb.id, "name": fb.name, "email": fb.email, "rating": fb.rating,
            "comment": fb.comment, "created": fb.created,
        }
