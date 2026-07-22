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
    packages = serializers.SerializerMethodField()

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

    def get_packages(self, obj):
        active_packages = [pkg for pkg in obj.packages.all() if pkg.is_active]
        return EditPackageSerializer(active_packages, many=True).data


class EditCategorySerializer(serializers.ModelSerializer):
    styles = serializers.SerializerMethodField()

    class Meta:
        model = EditCategory
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "styles",
        ]

    def get_styles(self, obj):
        active_styles = [style for style in obj.styles.all() if style.is_active]
        return EditStyleSerializer(active_styles, many=True, context=self.context).data