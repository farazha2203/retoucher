from django.db.models import Prefetch
from rest_framework import permissions, viewsets

from .models import EditorPortfolioItem, EditorProfile
from .serializers_editor import (
    EditorProfileDetailSerializer,
    EditorProfileListSerializer,
)


class EditorProfileViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EditorProfileDetailSerializer
        return EditorProfileListSerializer

    def get_queryset(self):
        active_portfolio = Prefetch(
            "portfolio_items",
            queryset=EditorPortfolioItem.objects.filter(
                is_active=True
            ).select_related("style"),
        )

        queryset = (
            EditorProfile.objects.filter(is_available=True)
            .select_related("user")
            .prefetch_related(
                "skills",
                "skills__category",
                "skills__packages",
                active_portfolio,
            )
            .order_by("-rating_average", "-completed_orders_count", "user__username")
        )

        skill = self.request.query_params.get("skill")
        if skill:
            queryset = queryset.filter(skills__slug=skill)

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(skills__category__slug=category)

        accepts_direct = self.request.query_params.get("accepts_direct")
        if accepts_direct in ["true", "1", "yes"]:
            queryset = queryset.filter(accepts_direct_requests=True)

        accepts_public = self.request.query_params.get("accepts_public")
        if accepts_public in ["true", "1", "yes"]:
            queryset = queryset.filter(accepts_public_requests=True)

        accepts_samples = self.request.query_params.get("accepts_samples")
        if accepts_samples in ["true", "1", "yes"]:
            queryset = queryset.filter(accepts_sample_challenges=True)

        return queryset.distinct()