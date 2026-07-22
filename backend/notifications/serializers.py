from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_username = serializers.CharField(
        source="recipient.username",
        read_only=True,
    )
    actor_username = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "recipient",
            "recipient_username",
            "actor",
            "actor_username",
            "notification_type",
            "priority",
            "title",
            "message",
            "data",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields

    def get_actor_username(self, obj):
        if obj.actor_id and obj.actor:
            return obj.actor.username
        return None