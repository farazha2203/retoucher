from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import (
    Order,
    OrderActivityLog,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderRating,
    OrderRevision,
    OrderStatusHistory,
    OrderNotification,
)


class OrderNotificationSerializer(serializers.ModelSerializer):
    order_title = serializers.CharField(
        source="order.title",
        read_only=True,
    )
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )
    recipient_username = serializers.CharField(
        source="recipient.username",
        read_only=True,
    )
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrderNotification
        fields = (
            "id",
            "order",
            "order_title",
            "activity_log",
            "actor",
            "actor_username",
            "recipient",
            "recipient_username",
            "notification_type",
            "title",
            "message",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields


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
            "order",
            "file",
            "note",
            "uploaded_by",
            "uploaded_by_username",
            "uploaded_at",
            "publication_status",
            "publication_requested_by",
            "publication_requested_at",
            "publication_reviewed_by",
            "publication_reviewed_at",
            "publication_note",
            "is_public",
        )
        read_only_fields = (
            "id",
            "order",
            "uploaded_by",
            "uploaded_by_username",
            "uploaded_at",
            "publication_status",
            "publication_requested_by",
            "publication_requested_at",
            "publication_reviewed_by",
            "publication_reviewed_at",
            "publication_note",
            "is_public",
        )

class PublicOrderDeliverySerializer(serializers.ModelSerializer):
    order_title = serializers.CharField(
        source="order.title",
        read_only=True,
    )
    uploaded_by_username = serializers.CharField(
        source="uploaded_by.username",
        read_only=True,
    )
    public_comments_count = serializers.SerializerMethodField()

    class Meta:
        model = OrderDelivery
        fields = (
            "id",
            "order",
            "order_title",
            "file",
            "note",
            "uploaded_by",
            "uploaded_by_username",
            "uploaded_at",
            "publication_status",
            "publication_reviewed_at",
            "is_public",
            "public_comments_count",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField)
    def get_public_comments_count(self, obj):
        annotated_count = getattr(obj, "public_comments_count", None)

        if annotated_count is not None:
            return annotated_count

        return OrderComment.objects.filter(
            status=OrderComment.Status.APPROVED,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=obj,
        ).count()




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

    parent_text = serializers.CharField(
        source="parent.text",
        read_only=True,
    )
    parent_sender_username = serializers.CharField(
        source="parent.sender.username",
        read_only=True,
    )

    resolved_by_username = serializers.CharField(
        source="resolved_by.username",
        read_only=True,
    )
    is_resolved = serializers.BooleanField(read_only=True)
    is_publicly_visible = serializers.BooleanField(read_only=True)

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
            "parent",
            "parent_text",
            "parent_sender_username",
            "is_resolved",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "annotation_type",
            "annotation_label",
            "annotation_color",
            "annotation_data",
            "is_publicly_visible",
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
            "is_resolved",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "is_publicly_visible",
        )

    def validate(self, attrs):
        order = self.context.get("order")

        if order is None and self.instance is not None:
            order = self.instance.order

        parent = attrs.get(
            "parent",
            getattr(self.instance, "parent", None),
        )

        if parent is not None:
            if getattr(parent, "status", None) == "deleted" and self.instance is None:
                raise serializers.ValidationError(
                    {"parent": "Cannot reply to a deleted comment."}
                )

            if order is not None and parent.order_id != order.id:
                raise serializers.ValidationError(
                    {"parent": "Parent comment must belong to the same order."}
                )

            attrs["target_type"] = parent.target_type
            attrs["image"] = parent.image
            attrs["delivery"] = parent.delivery
            attrs["revision"] = parent.revision

            # Reply does not inherit annotation unless explicitly provided.
            attrs.setdefault("annotation_type", "none")
            attrs.setdefault("annotation_label", "")
            attrs.setdefault("annotation_color", "")
            attrs.setdefault("annotation_data", {})

        target_type = attrs.get(
            "target_type",
            getattr(self.instance, "target_type", OrderComment.TargetType.ORDER),
        )
        image = attrs.get(
            "image",
            getattr(self.instance, "image", None),
        )
        delivery = attrs.get(
            "delivery",
            getattr(self.instance, "delivery", None),
        )
        revision = attrs.get(
            "revision",
            getattr(self.instance, "revision", None),
        )
        text = attrs.get(
            "text",
            getattr(self.instance, "text", ""),
        )
        x = attrs.get(
            "x",
            getattr(self.instance, "x", None),
        )
        y = attrs.get(
            "y",
            getattr(self.instance, "y", None),
        )

        if order is not None:
            if image is not None and image.order_id != order.id:
                raise serializers.ValidationError(
                    {"image": "Image must belong to the same order."}
                )

            if delivery is not None and delivery.order_id != order.id:
                raise serializers.ValidationError(
                    {"delivery": "Delivery must belong to the same order."}
                )

            if revision is not None and revision.order_id != order.id:
                raise serializers.ValidationError(
                    {"revision": "Revision must belong to the same order."}
                )

        relation_map = {
            OrderComment.TargetType.ORDER: [],
            OrderComment.TargetType.IMAGE: ["image"],
            OrderComment.TargetType.DELIVERY: ["delivery"],
            OrderComment.TargetType.REVISION: ["revision"],
        }

        if target_type not in relation_map:
            raise serializers.ValidationError({"target_type": "Invalid target_type."})

        required_fields = relation_map[target_type]
        actual_relations = {
            "image": image,
            "delivery": delivery,
            "revision": revision,
        }

        for field_name in required_fields:
            if actual_relations[field_name] is None:
                raise serializers.ValidationError(
                    {
                        field_name: f"This field is required when target_type is '{target_type}'."
                    }
                )

        for field_name, value in actual_relations.items():
            if field_name not in required_fields and value is not None:
                raise serializers.ValidationError(
                    {
                        field_name: f"This field must be empty when target_type is '{target_type}'."
                    }
                )

        if (x is None) != (y is None):
            raise serializers.ValidationError("Both x and y must be provided together.")

        if x is not None and not (0 <= x <= 100):
            raise serializers.ValidationError({"x": "x must be between 0 and 100."})

        if y is not None and not (0 <= y <= 100):
            raise serializers.ValidationError({"y": "y must be between 0 and 100."})

        if target_type == OrderComment.TargetType.ORDER and x is not None:
            raise serializers.ValidationError(
                "Coordinates are only allowed for image, delivery, or revision comments."
            )

        annotation_type = attrs.get(
            "annotation_type",
            getattr(self.instance, "annotation_type", "none"),
        )
        annotation_color = attrs.get(
            "annotation_color",
            getattr(self.instance, "annotation_color", ""),
        )
        annotation_data = attrs.get(
            "annotation_data",
            getattr(self.instance, "annotation_data", {}),
        )

        if annotation_type != "none":
            if target_type == OrderComment.TargetType.ORDER:
                raise serializers.ValidationError(
                    {
                        "annotation_type": "Order-level comments cannot use rich annotations."
                    }
                )

            if annotation_type == "point" and (x is None or y is None):
                raise serializers.ValidationError(
                    {
                        "annotation_type": "Point annotations require x and y coordinates."
                    }
                )

        if annotation_color:
            if not isinstance(annotation_color, str):
                raise serializers.ValidationError(
                    {"annotation_color": "Annotation color must be a string."}
                )

            if len(annotation_color) > 20:
                raise serializers.ValidationError(
                    {"annotation_color": "Annotation color is too long."}
                )

        if annotation_data is None:
            attrs["annotation_data"] = {}
        elif not isinstance(annotation_data, dict):
            raise serializers.ValidationError(
                {"annotation_data": "Annotation data must be a JSON object."}
            )

        if not (text or "").strip() and x is None and y is None:
            raise serializers.ValidationError(
                {"text": "Comment must have text or coordinate annotation."}
            )

        return attrs


class OrderCommentThreadSerializer(OrderCommentSerializer):
    replies = serializers.SerializerMethodField()

    class Meta(OrderCommentSerializer.Meta):
        fields = OrderCommentSerializer.Meta.fields + ("replies",)

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_replies(self, obj) -> list:
        replies = obj.replies.all()

        replies = sorted(
            replies,
            key=lambda reply: reply.created_at,
        )

        return OrderCommentThreadSerializer(
            replies,
            many=True,
            context=self.context,
        ).data
    
class PublicOrderDeliveryDetailSerializer(PublicOrderDeliverySerializer):
    public_comments = serializers.SerializerMethodField()

    class Meta(PublicOrderDeliverySerializer.Meta):
        fields = PublicOrderDeliverySerializer.Meta.fields + (
            "public_comments",
        )

    @extend_schema_field(OrderCommentSerializer(many=True))
    def get_public_comments(self, obj):
        comments = (
            obj.comments.select_related(
                "sender",
                "resolved_by",
                "parent",
                "parent__sender",
                "delivery",
            )
            .filter(
                status=OrderComment.Status.APPROVED,
                target_type=OrderComment.TargetType.DELIVERY,
                delivery=obj,
            )
            .exclude(status=OrderComment.Status.DELETED)
            .order_by("created_at")
        )

        return OrderCommentSerializer(
            comments,
            many=True,
            context=self.context,
        ).data
    
class PublicEditorPortfolioUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)


class PublicEditorPortfolioStatsSerializer(serializers.Serializer):
    public_deliveries_count = serializers.IntegerField()
    public_comments_count = serializers.IntegerField()


class PublicEditorPortfolioRatingSerializer(serializers.Serializer):
    average = serializers.FloatField()
    count = serializers.IntegerField()


class PublicEditorPortfolioSerializer(serializers.Serializer):
    editor = PublicEditorPortfolioUserSerializer()
    stats = PublicEditorPortfolioStatsSerializer()
    rating = PublicEditorPortfolioRatingSerializer()
    deliveries = PublicOrderDeliverySerializer(many=True)


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
