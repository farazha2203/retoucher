from django.db.models import Prefetch
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EditorPortfolioItem, EditorProfile
from .editor_workspace_mixin import EditorWorkspaceActionsMixin
from .serializers_editor import (
    EditorProfileDetailSerializer,
    EditorProfileListSerializer,
)


class EditorProfileViewSet(EditorWorkspaceActionsMixin, viewsets.ReadOnlyModelViewSet):
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

    @action(detail=False, methods=("get", "patch"), permission_classes=(permissions.IsAuthenticated,), url_path="me")
    def me(self, request):
        profile = EditorProfile.objects.filter(user=request.user).first()
        if profile is None:
            return Response({"detail": "پروفایل ادیتور وجود ندارد."}, status=status.HTTP_404_NOT_FOUND)
        if request.method == "GET":
            return Response(EditorProfileDetailSerializer(profile, context={"request": request}).data)

        for field in (
            "display_name", "bio", "base_price", "average_delivery_hours",
            "is_available", "accepts_direct_requests",
            "accepts_public_requests", "accepts_sample_challenges",
        ):
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save()
        return Response(EditorProfileDetailSerializer(profile, context={"request": request}).data)

    @action(detail=False, methods=("post",), permission_classes=(permissions.IsAuthenticated,), url_path="me/portfolio")
    def create_portfolio_item(self, request):
        profile = EditorProfile.objects.filter(user=request.user).first()
        if profile is None:
            return Response({"detail": "پروفایل ادیتور وجود ندارد."}, status=status.HTTP_404_NOT_FOUND)

        title = str(request.data.get("title") or "").strip()
        if not title:
            return Response({"title": ["عنوان الزامی است."]}, status=status.HTTP_400_BAD_REQUEST)

        item = EditorPortfolioItem.objects.create(
            editor=profile,
            title=title,
            description=request.data.get("description", ""),
            before_image=request.FILES.get("before_image"),
            after_image=request.FILES.get("after_image"),
            is_active=False,
        )
        return Response({"id": item.id, "status": "created_pending_review"}, status=status.HTTP_201_CREATED)

