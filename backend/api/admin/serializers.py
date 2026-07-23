from rest_framework import serializers


class ModerateSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class StatsSerializer(serializers.Serializer):
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    hidden = serializers.IntegerField()
    rejected = serializers.IntegerField()
    total = serializers.IntegerField()
