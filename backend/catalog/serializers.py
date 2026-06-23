from rest_framework import serializers

from .models import EditCategory, EditPackage, EditStyle


class EditPackageSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = EditPackage
        fields = [
            "id",
            "title",
            "level",
            "level_display",
            "description",
            "price",
            "min_images",
            "max_images",
            "estimated_delivery_hours",
            "includes_revision",
            "revision_count",
        ]


class EditStyleSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(source="category.title", read_only=True)
    packages = EditPackageSerializer(many=True, read_only=True)

    class Meta:
        model = EditStyle
        fields = [
            "id",
            "category",
            "category_title",
            "title",
            "slug",
            "description",
            "min_price",
            "max_price",
            "suggested_price",
            "estimated_delivery_hours",
            "packages",
        ]


class EditCategorySerializer(serializers.ModelSerializer):
    styles = EditStyleSerializer(many=True, read_only=True)

    class Meta:
        model = EditCategory
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "styles",
        ]