from rest_framework import serializers


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class DashboardSummarySerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    open_orders = serializers.IntegerField()
    closed_orders = serializers.IntegerField()
    unassigned_orders = serializers.IntegerField()
    overdue_orders = serializers.IntegerField()
    due_soon_orders = serializers.IntegerField()
    due_soon_days = serializers.IntegerField()
    settlement_pending_orders = serializers.IntegerField()
    paid_orders = serializers.IntegerField()


class DeadlineSummarySerializer(serializers.Serializer):
    overdue_orders = serializers.IntegerField()
    due_today_orders = serializers.IntegerField()
    due_soon_orders = serializers.IntegerField()
    due_soon_days = serializers.IntegerField()


class StatusSummaryItemSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class SettlementSummarySerializer(serializers.Serializer):
    completed_orders = serializers.IntegerField()
    settlement_pending_orders = serializers.IntegerField()
    paid_orders = serializers.IntegerField()
    closed_orders = serializers.IntegerField()
    settlement_pipeline_total = serializers.IntegerField()


class EditorWorkloadItemSerializer(serializers.Serializer):
    editor = serializers.IntegerField()
    editor_username = serializers.CharField()
    total_orders = serializers.IntegerField()
    active_orders = serializers.IntegerField()
    closed_orders = serializers.IntegerField()
    delivered_orders = serializers.IntegerField()
    in_progress_orders = serializers.IntegerField()
    revision_required_orders = serializers.IntegerField()


class AssignEditorRequestSerializer(serializers.Serializer):
    editor_id = serializers.IntegerField()


class NoteRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class DeliveryUploadRequestSerializer(serializers.Serializer):
    file = serializers.FileField()
    note = serializers.CharField(required=False, allow_blank=True)


class ImageUploadRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    note = serializers.CharField(required=False, allow_blank=True)


class RatingRequestSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=10)
    comment = serializers.CharField(required=False, allow_blank=True)


class CommentCreateRequestSerializer(serializers.Serializer):
    parent = serializers.IntegerField(required=False)
    target_type = serializers.ChoiceField(
        choices=("order", "image", "delivery", "revision"),
        required=False,
    )
    image = serializers.IntegerField(required=False)
    delivery = serializers.IntegerField(required=False)
    revision = serializers.IntegerField(required=False)
    text = serializers.CharField()
    x = serializers.FloatField(required=False)
    y = serializers.FloatField(required=False)

    annotation_type = serializers.ChoiceField(
        choices=("none", "point", "rectangle", "circle", "arrow", "freehand"),
        required=False,
    )
    annotation_label = serializers.CharField(required=False, allow_blank=True)
    annotation_color = serializers.CharField(required=False, allow_blank=True)
    annotation_data = serializers.JSONField(required=False)


class CommentUpdateRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=False)
    x = serializers.FloatField(required=False)
    y = serializers.FloatField(required=False)
    status = serializers.CharField(required=False)

    annotation_type = serializers.ChoiceField(
        choices=("none", "point", "rectangle", "circle", "arrow", "freehand"),
        required=False,
    )
    annotation_label = serializers.CharField(required=False, allow_blank=True)
    annotation_color = serializers.CharField(required=False, allow_blank=True)
    annotation_data = serializers.JSONField(required=False)


class CommentStatusRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=("active", "approved", "rejected", "deleted"),
    )


class NotificationUnreadCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()


class MarkAllNotificationsReadResponseSerializer(serializers.Serializer):
    updated_count = serializers.IntegerField()
    read_at = serializers.DateTimeField()