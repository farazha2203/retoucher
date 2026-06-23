from rest_framework import serializers

from .models import Order, OrderDelivery, OrderImage, OrderRating, OrderRevision


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
        )
        read_only_fields = (
            "id",
            "source",
            "rated_by",
            "rated_by_username",
            "created_at",
        )

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Score must be between 1 and 10.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    images = OrderImageSerializer(many=True, read_only=True)
    deliveries = OrderDeliverySerializer(many=True, read_only=True)
    revisions = OrderRevisionSerializer(many=True, read_only=True)
    ratings = OrderRatingSerializer(many=True, read_only=True)
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
            "created_at",
            "updated_at",
        )