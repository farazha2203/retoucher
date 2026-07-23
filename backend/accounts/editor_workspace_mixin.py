from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EditorPortfolioItem, EditorProfile
from .serializers_editor import EditorProfileDetailSerializer


class EditorWorkspaceActionsMixin:
    def _my_profile(self, request):
        return EditorProfile.objects.filter(user=request.user).first()

    @action(detail=False, methods=("get", "patch"), permission_classes=(permissions.IsAuthenticated,), url_path="me")
    def me(self, request):
        profile = self._my_profile(request)
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
        profile = self._my_profile(request)
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
            review_status=EditorPortfolioItem.ReviewStatus.DRAFT,
        )
        return Response(self._portfolio_payload(item), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=("patch", "delete"), permission_classes=(permissions.IsAuthenticated,), url_path=r"me/portfolio/(?P<portfolio_id>[^/.]+)")
    def portfolio_item(self, request, portfolio_id=None):
        profile = self._my_profile(request)
        item = get_object_or_404(EditorPortfolioItem, pk=portfolio_id, editor=profile)

        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if item.review_status == EditorPortfolioItem.ReviewStatus.PENDING:
            return Response({"detail": "نمونه‌کار در حال بررسی است."}, status=status.HTTP_409_CONFLICT)

        for field in ("title", "description"):
            if field in request.data:
                setattr(item, field, request.data[field])
        if "before_image" in request.FILES:
            item.before_image = request.FILES["before_image"]
        if "after_image" in request.FILES:
            item.after_image = request.FILES["after_image"]

        item.review_status = EditorPortfolioItem.ReviewStatus.DRAFT
        item.is_active = False
        item.review_note = ""
        item.reviewed_by = None
        item.reviewed_at = None
        item.save()
        return Response(self._portfolio_payload(item))

    @action(detail=False, methods=("post",), permission_classes=(permissions.IsAuthenticated,), url_path=r"me/portfolio/(?P<portfolio_id>[^/.]+)/submit")
    def submit_portfolio_item(self, request, portfolio_id=None):
        profile = self._my_profile(request)
        item = get_object_or_404(EditorPortfolioItem, pk=portfolio_id, editor=profile)

        if not item.before_image or not item.after_image:
            return Response({"detail": "تصویر قبل و بعد الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        item.review_status = EditorPortfolioItem.ReviewStatus.PENDING
        item.is_active = False
        item.review_note = ""
        item.reviewed_by = None
        item.reviewed_at = None
        item.save()
        return Response(self._portfolio_payload(item))

    def _portfolio_payload(self, item):
        return {
            "id": item.pk,
            "title": item.title,
            "description": item.description,
            "before_image": item.before_image.url if item.before_image else None,
            "after_image": item.after_image.url if item.after_image else None,
            "is_active": item.is_active,
            "is_featured": item.is_featured,
            "review_status": item.review_status,
            "review_note": item.review_note,
        }
