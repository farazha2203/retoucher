from __future__ import annotations

from django.db import models
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    EditorPortfolioItem,
    PortfolioComment,
    PortfolioCommentReport,
    PortfolioLike,
)


class PortfolioCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioComment
        fields = (
            "id",
            "username",
            "body",
            "status",
            "is_edited",
            "created_at",
            "replies",
        )
        read_only_fields = fields

    def get_replies(self, obj):
        replies = obj.replies.filter(
            status=PortfolioComment.Status.APPROVED
        ).select_related("user")
        return PortfolioCommentSerializer(replies, many=True).data


class PortfolioSocialSerializer(serializers.ModelSerializer):
    editor_id = serializers.IntegerField(source="editor_id", read_only=True)
    editor_name = serializers.CharField(
        source="editor.display_name",
        read_only=True,
    )
    style_title = serializers.CharField(
        source="style.title",
        read_only=True,
        allow_null=True,
    )
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = EditorPortfolioItem
        fields = (
            "id",
            "editor_id",
            "editor_name",
            "title",
            "description",
            "style_title",
            "before_image",
            "after_image",
            "is_featured",
            "likes_count",
            "comments_count",
            "is_liked",
            "comments",
        )

    def get_comments(self, obj):
        comments = obj.social_comments.filter(
            status=PortfolioComment.Status.APPROVED,
            parent__isnull=True,
        ).select_related("user")
        return PortfolioCommentSerializer(comments, many=True).data


class PortfolioSocialViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioSocialSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        user = self.request.user
        liked = (
            PortfolioLike.objects.filter(
                portfolio_item=OuterRef("pk"),
                user=user,
            )
            if user.is_authenticated
            else PortfolioLike.objects.none()
        )

        return (
            EditorPortfolioItem.objects.filter(is_active=True)
            .select_related("editor", "editor__user", "style")
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count(
                    "social_comments",
                    filter=Q(
                        social_comments__status=PortfolioComment.Status.APPROVED
                    ),
                    distinct=True,
                ),
                is_liked=Exists(liked),
            )
            .order_by("-is_featured", "sort_order", "-created_at")
        )

    @action(
        detail=True,
        methods=("post",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def toggle_like(self, request, pk=None):
        item = self.get_object()
        like, created = PortfolioLike.objects.get_or_create(
            portfolio_item=item,
            user=request.user,
        )
        if not created:
            like.delete()

        count = PortfolioLike.objects.filter(
            portfolio_item=item
        ).count()
        return Response({"liked": created, "likes_count": count})

    @action(
        detail=True,
        methods=("post",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def comment(self, request, pk=None):
        item = self.get_object()
        body = str(request.data.get("body") or "").strip()
        parent_id = request.data.get("parent")

        if len(body) < 2:
            return Response(
                {"body": ["متن دیدگاه بسیار کوتاه است."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parent = None
        if parent_id:
            parent = PortfolioComment.objects.filter(
                pk=parent_id,
                portfolio_item=item,
                parent__isnull=True,
                status=PortfolioComment.Status.APPROVED,
            ).first()
            if parent is None:
                return Response(
                    {"parent": ["دیدگاه والد معتبر نیست."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        comment = PortfolioComment.objects.create(
            portfolio_item=item,
            user=request.user,
            parent=parent,
            body=body,
        )
        return Response(
            PortfolioCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=("post",),
        url_path="report-comment",
        permission_classes=(permissions.IsAuthenticated,),
    )
    def report_comment(self, request, pk=None):
        item = self.get_object()
        comment_id = request.data.get("comment")
        reason = str(request.data.get("reason") or "").strip()

        comment = PortfolioComment.objects.filter(
            pk=comment_id,
            portfolio_item=item,
            status=PortfolioComment.Status.APPROVED,
        ).first()
        if comment is None:
            return Response(
                {"comment": ["دیدگاه معتبر نیست."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(reason) < 3:
            return Response(
                {"reason": ["علت گزارش را وارد کنید."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report, created = PortfolioCommentReport.objects.get_or_create(
            comment=comment,
            reporter=request.user,
            defaults={"reason": reason},
        )
        return Response(
            {"created": created, "report_id": report.pk},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PortfolioCommentModerationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioCommentSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return PortfolioComment.objects.select_related(
            "user",
            "portfolio_item",
            "portfolio_item__editor",
        ).order_by("-created_at")

    @action(detail=True, methods=("post",))
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.status = PortfolioComment.Status.APPROVED
        comment.moderated_by = request.user
        comment.moderated_at = timezone.now()
        comment.save(
            update_fields=("status", "moderated_by", "moderated_at", "updated_at")
        )
        return Response(self.get_serializer(comment).data)

    @action(detail=True, methods=("post",))
    def hide(self, request, pk=None):
        comment = self.get_object()
        comment.status = PortfolioComment.Status.HIDDEN
        comment.moderated_by = request.user
        comment.moderated_at = timezone.now()
        comment.save(
            update_fields=("status", "moderated_by", "moderated_at", "updated_at")
        )
        return Response(self.get_serializer(comment).data)
