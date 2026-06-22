from rest_framework import serializers

from .models import Order, OrderImage


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


class OrderSerializer(serializers.ModelSerializer):
    images = OrderImageSerializer(many=True, read_only=True)
    client_username = serializers.CharField(
        source="client.username",
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "client",
            "client_username",
            "title",
            "description",
            "status",
            "deadline",
            "images",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "client",
            "client_username",
            "status",
            "images",
            "created_at",
            "updated_at",
        )