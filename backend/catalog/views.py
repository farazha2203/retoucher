from rest_framework import permissions, viewsets

from .models import EditCategory, EditPackage, EditStyle
from .serializers import (
    EditCategorySerializer,
    EditPackageSerializer,
    EditStyleSerializer,
)


class EditCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EditCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            EditCategory.objects.filter(is_active=True)
            .prefetch_related(
                "styles",
                "styles__packages",
            )
            .order_by("sort_order", "title")
        )


class EditStyleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EditStyleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            EditStyle.objects.filter(is_active=True, category__is_active=True)
            .select_related("category")
            .prefetch_related("packages")
            .order_by("category__sort_order", "sort_order", "title")
        )

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        return queryset


class EditPackageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EditPackageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = (
            EditPackage.objects.filter(
                is_active=True,
                style__is_active=True,
                style__category__is_active=True,
            )
            .select_related("style", "style__category")
            .order_by("style__category__sort_order", "style__sort_order", "sort_order", "price")
        )

        style = self.request.query_params.get("style")
        if style:
            queryset = queryset.filter(style__slug=style)

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(style__category__slug=category)

        return queryset