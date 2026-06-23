from rest_framework import serializers

from .models import (
    Order,
    OrderActivityLog,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderRating,
    OrderRevision,
    OrderStatusHistory,
)


class OrderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderImage
        fields = (
            "id",
            "image",
            "note",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "uploaded_at",
        )


class OrderDeliverySerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(
        source="uploaded_by.username",
        read_only=True,
    )

    class Meta:
        model = OrderDelivery
        fields = (
            "id",
            "file",
            "note",
            "uploaded_by",
            "uploaded_by_username",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "uploaded_by",
            "uploaded_by_username",
            "uploaded_at",
        )


class OrderRevisionSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(
        source="requested_by.username",
        read_only=True,
    )

    def validate_note(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Revision note cannot be empty.")
        return value

    class Meta:
        model = OrderRevision
        fields = (
            "id",
            "source",
            "note",
            "requested_by",
            "requested_by_username",
            "created_at",
        )
        read_only_fields = (
            "id",
            "source",
            "requested_by",
            "requested_by_username",
            "created_at",
        )


class OrderRatingSerializer(serializers.ModelSerializer):
    rated_by_username = serializers.CharField(
        source="rated_by.username",
        read_only=True,
    )

    def validate_score(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError("Score must be between 1 and 10.")
        return value

    def validate_comment(self, value):
        return (value or "").strip()

    class Meta:
        model = OrderRating
        fields = (
            "id",
            "source",
            "score",
            "comment",
            "rated_by",
            "rated_by_username",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "source",
            "rated_by",
            "rated_by_username",
            "created_at",
            "updated_at",
        )

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Score must be between 1 and 10.")
        return value
    
class OrderCommentSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True,
    )

    def validate(self, attrs):
        target_type = attrs.get("target_type", getattr(self.instance, "target_type", None))
        image = attrs.get("image", getattr(self.instance, "image", None))
        delivery = attrs.get("delivery", getattr(self.instance, "delivery", None))
        revision = attrs.get("revision", getattr(self.instance, "revision", None))
        text = attrs.get("text", getattr(self.instance, "text", ""))
        x = attrs.get("x", getattr(self.instance, "x", None))
        y = attrs.get("y", getattr(self.instance, "y", None))

        relation_map = {
            "order": [],
            "image": ["image"],
            "delivery": ["delivery"],
            "revision": ["revision"],
        }

        required_fields = relation_map.get(target_type, [])
        actual_relations = {
            "image": image,
            "delivery": delivery,
            "revision": revision,
        }

        for field_name in required_fields:
            if actual_relations[field_name] is None:
                raise serializers.ValidationError(
                    {field_name: f"This field is required when target_type is '{target_type}'."}
                )

        for field_name, value in actual_relations.items():
            if field_name not in required_fields and value is not None:
                raise serializers.ValidationError(
                    {field_name: f"This field must be empty when target_type is '{target_type}'."}
                )

        if (x is None) != (y is None):
            raise serializers.ValidationError("Both x and y must be provided together.")

        if x is not None and not (0 <= x <= 100):
            raise serializers.ValidationError({"x": "x must be between 0 and 100."})

        if y is not None and not (0 <= y <= 100):
            raise serializers.ValidationError({"y": "y must be between 0 and 100."})

        if target_type == "order" and x is not None:
            raise serializers.ValidationError(
                "Coordinates are only allowed for image, delivery, or revision comments."
            )

        if not (text or "").strip() and x is None and y is None:
            raise serializers.ValidationError(
                {"text": "Comment must have text or coordinate annotation."}
            )

        return attrs

    class Meta:
        model = OrderComment
        fields = (
            "id",
            "order",
            "sender",
            "sender_username",
            "target_type",
            "image",
            "delivery",
            "revision",
            "text",
            "x",
            "y",
            "status",
            "is_edited",
            "edited_at",
            "deleted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "order",
            "sender",
            "sender_username",
            "status",
            "is_edited",
            "edited_at",
            "deleted_at",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        target_type = attrs.get("target_type", OrderComment.TargetType.ORDER)
        image = attrs.get("image")
        delivery = attrs.get("delivery")
        revision = attrs.get("revision")

        if target_type == OrderComment.TargetType.ORDER:
            if image or delivery or revision:
                raise serializers.ValidationError(
                    "Order comments must not include image, delivery, or revision."
                )

        if target_type == OrderComment.TargetType.IMAGE and not image:
            raise serializers.ValidationError(
                "Image comments require an image."
            )

        if target_type == OrderComment.TargetType.DELIVERY and not delivery:
            raise serializers.ValidationError(
                "Delivery comments require a delivery."
            )

        if target_type == OrderComment.TargetType.REVISION and not revision:
            raise serializers.ValidationError(
                "Revision comments require a revision."
            )

        return attrs

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(
        source="changed_by.username",
        read_only=True,
    )

    class Meta:
        model = OrderStatusHistory
        fields = (
            "id",
            "order",
            "changed_by",
            "changed_by_username",
            "from_status",
            "to_status",
            "note",
            "created_at",
        )
        read_only_fields = fields

class OrderActivityLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )

    class Meta:
        model = OrderActivityLog
        fields = (
            "id",
            "order",
            "actor",
            "actor_username",
            "activity_type",
            "message",
            "metadata",
            "created_at",
        )
        read_only_fields = fields

class OrderListSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(
        source="client.username",
        read_only=True,
    )
    editor_username = serializers.CharField(
        source="editor.username",
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "client",
            "client_username",
            "editor",
            "editor_username",
            "title",
            "status",
            "revision_count",
            "deadline",
            "supervisor_approved_at",
            "client_approved_at",
            "settlement_started_at",
            "paid_at",
            "closed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

        
class OrderSerializer(serializers.ModelSerializer):
    images = OrderImageSerializer(many=True, read_only=True)
    deliveries = OrderDeliverySerializer(many=True, read_only=True)
    revisions = OrderRevisionSerializer(many=True, read_only=True)
    ratings = OrderRatingSerializer(many=True, read_only=True)
    comments = OrderCommentSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    activity_logs = OrderActivityLogSerializer(many=True, read_only=True)
    client_username = serializers.CharField(
        source="client.username",
        read_only=True,
    )
    editor_username = serializers.CharField(
        source="editor.username",
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "client",
            "client_username",
            "editor",
            "editor_username",
            "title",
            "description",
            "status",
            "revision_count",
            "supervisor_approved_at",
            "client_approved_at",
            "deadline",
            "images",
            "deliveries",
            "revisions",
            "ratings",
            "comments",
            "status_history",
            "activity_logs",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "client",
            "client_username",
            "editor",
            "editor_username",
            "status",
            "revision_count",
            "supervisor_approved_at",
            "client_approved_at",
            "images",
            "deliveries",
            "revisions",
            "ratings",
            "comments",
            "status_history",
            "activity_logs",
            "created_at",
            "updated_at",
        )