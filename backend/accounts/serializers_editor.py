from rest_framework import serializers

from catalog.serializers import EditStyleSerializer

from .models import EditorPortfolioItem, EditorProfile


class EditorPortfolioItemSerializer(serializers.ModelSerializer):
    style_title = serializers.CharField(source="style.title", read_only=True)

    class Meta:
        model = EditorPortfolioItem
        fields = [
            "id",
            "title",
            "description",
            "style",
            "style_title",
            "before_image",
            "after_image",
            "is_featured",
            "review_note",
            "review_status",
        ]


class EditorProfileListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    skills = EditStyleSerializer(many=True, read_only=True)

    class Meta:
        model = EditorProfile
        fields = [
            "id",
            "user",
            "username",
            "display_name",
            "bio",
            "level",
            "skills",
            "base_price",
            "average_delivery_hours",
            "rating_average",
            "completed_orders_count",
            "is_available",
            "accepts_direct_requests",
            "accepts_public_requests",
            "accepts_sample_challenges",
        ]


class EditorProfileDetailSerializer(EditorProfileListSerializer):
    portfolio_items = EditorPortfolioItemSerializer(many=True, read_only=True)

    class Meta(EditorProfileListSerializer.Meta):
        fields = EditorProfileListSerializer.Meta.fields + [
            "portfolio_items",
        ]