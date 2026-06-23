from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from django.db import models
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)

from .api_docs import (
    AssignEditorRequestSerializer,
    CommentCreateRequestSerializer,
    CommentStatusRequestSerializer,
    CommentUpdateRequestSerializer,
    DashboardSummarySerializer,
    DeadlineSummarySerializer,
    DeliveryUploadRequestSerializer,
    DetailResponseSerializer,
    EditorWorkloadItemSerializer,
    ImageUploadRequestSerializer,
    MarkAllNotificationsReadResponseSerializer,
    NoteRequestSerializer,
    NotificationUnreadCountSerializer,
    RatingRequestSerializer,
    SettlementSummarySerializer,
    StatusSummaryItemSerializer,
)


from .models import (
    Order,
    OrderActivityLog,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderRating,
    OrderRevision,
    OrderStatusHistory,
    OrderNotification,
)
from .permissions import CanCreateOrder, IsOrderOwnerOrStaffRole
from .serializers import (
    OrderActivityLogSerializer,
    OrderCommentSerializer,
    OrderCommentThreadSerializer,
    OrderDeliverySerializer,
    OrderImageSerializer,
    OrderListSerializer,
    OrderRatingSerializer,
    OrderRevisionSerializer,
    OrderSerializer,
    OrderStatusHistorySerializer,
    OrderNotificationSerializer,
)

User = get_user_model()


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanCreateOrder,
        IsOrderOwnerOrStaffRole,
    )
    pagination_class = OrderPagination
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = (
        "title",
        "description",
        "client__username",
        "editor__username",
    )
    ordering_fields = (
        "id",
        "created_at",
        "updated_at",
        "deadline",
        "status",
    )
    ordering = ("-created_at",)

    def _get_order_comment(self, order, comment_id):
        return get_object_or_404(
            order.comments.select_related(
                "sender",
                "resolved_by",
                "parent",
                "parent__sender",
            ),
            pk=comment_id,
        )

    def _parse_positive_int_query_param(self, value, field_name, default):
        if value in [None, ""]:
            return default

        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            raise ValidationError(
                {field_name: "This query parameter must be a positive integer."}
            )

        if parsed_value <= 0:
            raise ValidationError(
                {field_name: "This query parameter must be a positive integer."}
            )

        return parsed_value

    def _parse_bool_query_param(self, value):
        if value is None:
            return None

        normalized = str(value).strip().lower()

        if normalized in {"true", "1", "yes", "y"}:
            return True

        if normalized in {"false", "0", "no", "n"}:
            return False

        raise ValidationError(
            {"detail": f"Invalid boolean query parameter value: {value}"}
        )

    def _parse_datetime_query_param(self, value, field_name, end_of_day=False):
        if not value:
            return None

        parsed_datetime = parse_datetime(value)

        if parsed_datetime is not None:
            if timezone.is_naive(parsed_datetime):
                parsed_datetime = timezone.make_aware(
                    parsed_datetime,
                    timezone.get_current_timezone(),
                )
            return parsed_datetime

        parsed_date = parse_date(value)

        if parsed_date is not None:
            parsed_time = time.max if end_of_day else time.min
            parsed_datetime = datetime.combine(parsed_date, parsed_time)
            return timezone.make_aware(
                parsed_datetime,
                timezone.get_current_timezone(),
            )

        raise ValidationError(
            {
                field_name: "Invalid date/datetime format. Use YYYY-MM-DD or ISO datetime."
            }
        )

    def _apply_order_filters(self, queryset):
        params = self.request.query_params

        status_param = params.get("status")
        client_param = params.get("client") or params.get("client_id")
        editor_param = params.get("editor") or params.get("editor_id")
        unassigned_param = params.get("unassigned")
        mine_param = params.get("mine")
        assigned_to_me_param = params.get("assigned_to_me")

        deadline_after = self._parse_datetime_query_param(
            params.get("deadline_after"),
            "deadline_after",
        )
        deadline_before = self._parse_datetime_query_param(
            params.get("deadline_before"),
            "deadline_before",
            end_of_day=True,
        )
        created_after = self._parse_datetime_query_param(
            params.get("created_after"),
            "created_after",
        )
        created_before = self._parse_datetime_query_param(
            params.get("created_before"),
            "created_before",
            end_of_day=True,
        )
        updated_after = self._parse_datetime_query_param(
            params.get("updated_after"),
            "updated_after",
        )
        updated_before = self._parse_datetime_query_param(
            params.get("updated_before"),
            "updated_before",
            end_of_day=True,
        )

        if status_param:
            statuses = [
                item.strip() for item in status_param.split(",") if item.strip()
            ]
            queryset = queryset.filter(status__in=statuses)

        if client_param:
            queryset = queryset.filter(client_id=client_param)

        if editor_param:
            queryset = queryset.filter(editor_id=editor_param)

        unassigned = self._parse_bool_query_param(unassigned_param)
        if unassigned is True:
            queryset = queryset.filter(editor__isnull=True)

        mine = self._parse_bool_query_param(mine_param)
        if mine is True:
            user = self.request.user

            if self._is_staff_role(user):
                # Staff can see all orders by default.
                # So mine=true does not narrow staff results.
                pass
            else:
                queryset = queryset.filter(
                    models.Q(client=user) | models.Q(editor=user)
                )

        assigned_to_me = self._parse_bool_query_param(assigned_to_me_param)
        if assigned_to_me is True:
            queryset = queryset.filter(editor=self.request.user)

        if deadline_after:
            queryset = queryset.filter(deadline__gte=deadline_after)

        if deadline_before:
            queryset = queryset.filter(deadline__lte=deadline_before)

        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)

        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)

        if updated_after:
            queryset = queryset.filter(updated_at__gte=updated_after)

        if updated_before:
            queryset = queryset.filter(updated_at__lte=updated_before)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return super().get_serializer_class()

    def _save_or_update_rating(self, order, user, source, serializer):
        ratings = OrderRating.objects.filter(
            order=order,
            rated_by=user,
            source=source,
        ).order_by("-created_at")

        rating = ratings.first()

        if rating:
            rating.score = serializer.validated_data["score"]
            rating.comment = serializer.validated_data.get("comment", "")
            rating.save(update_fields=["score", "comment", "updated_at"])
            return rating

        return OrderRating.objects.create(
            order=order,
            rated_by=user,
            source=source,
            score=serializer.validated_data["score"],
            comment=serializer.validated_data.get("comment", ""),
        )

    def _log_status_change(self, order, user, from_status, to_status, note=""):
        OrderStatusHistory.objects.create(
            order=order,
            changed_by=user,
            from_status=from_status or "",
            to_status=to_status,
            note=note,
        )

    def _get_order_notification_recipients(self, order, actor=None):
        recipients = []

        if order.client_id:
            recipients.append(order.client)

        if order.editor_id:
            recipients.append(order.editor)

        unique_recipients = []
        seen_ids = set()

        for user in recipients:
            if user is None:
                continue

            if actor is not None and user.id == actor.id:
                continue

            if user.id in seen_ids:
                continue

            seen_ids.add(user.id)
            unique_recipients.append(user)

        return unique_recipients

    def _build_notification_title(self, activity_type):
        title_map = {
            "comment_created": "New comment",
            "comment_updated": "Comment updated",
            "comment_deleted": "Comment deleted",
            "comment_resolved": "Comment resolved",
            "comment_unresolved": "Comment unresolved",
            "editor_assigned": "Editor assigned",
            "delivery_uploaded": "New delivery uploaded",
            "revision_requested": "Revision requested",
            "rating_created": "Rating submitted",
            "rating_updated": "Rating updated",
            "status_changed": "Order status changed",
        }

        return title_map.get(activity_type, "New activity on order")

    def _create_order_notifications(
        self,
        order,
        actor,
        activity_log,
        activity_type,
        message,
        metadata=None,
    ):
        recipients = self._get_order_notification_recipients(
            order=order,
            actor=actor,
        )

        notifications = []

        for recipient in recipients:
            notifications.append(
                OrderNotification(
                    recipient=recipient,
                    actor=actor if getattr(actor, "is_authenticated", False) else None,
                    order=order,
                    activity_log=activity_log,
                    notification_type=activity_type,
                    title=self._build_notification_title(activity_type),
                    message=message or "",
                    metadata=metadata or {},
                )
            )

        if notifications:
            OrderNotification.objects.bulk_create(notifications)

    def _log_activity(self, order, actor, activity_type, message, metadata=None):
        activity_log = OrderActivityLog.objects.create(
            order=order,
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            activity_type=activity_type,
            message=message,
            metadata=metadata or {},
        )

        self._create_order_notifications(
            order=order,
            actor=actor,
            activity_log=activity_log,
            activity_type=activity_type,
            message=message,
            metadata=metadata or {},
        )

        return activity_log

    def _update_order_status(
        self, order, new_status, user, note="", extra_updates=None
    ):
        from_status = order.status

        order.status = new_status
        update_fields = {"status", "updated_at"}

        if extra_updates:
            for field_name, value in extra_updates.items():
                setattr(order, field_name, value)
                update_fields.add(field_name)

        order.save(update_fields=list(update_fields))
        self._log_status_change(
            order=order,
            user=user,
            from_status=from_status,
            to_status=new_status,
            note=note,
        )

    @extend_schema(
        tags=["Order Dashboard"],
        summary="Get order count grouped by status",
        parameters=[
            OpenApiParameter(
                "client", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "editor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "status", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={200: StatusSummaryItemSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="status-summary",
    )
    def status_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        summary = (
            queryset.values("status")
            .annotate(count=models.Count("id"))
            .order_by("status")
        )

        return Response(list(summary), status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Notifications"],
        summary="List current user's order notifications",
        parameters=[
            OpenApiParameter(
                "unread", OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "order", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "order_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "type", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "notification_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: OrderNotificationSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="notifications",
    )
    def notifications(self, request):
        queryset = (
            OrderNotification.objects.select_related(
                "order",
                "actor",
                "recipient",
                "activity_log",
            )
            .filter(recipient=request.user)
            .order_by("-created_at")
        )

        unread_param = request.query_params.get("unread")
        unread = self._parse_bool_query_param(unread_param)

        if unread is True:
            queryset = queryset.filter(read_at__isnull=True)

        if unread is False:
            queryset = queryset.filter(read_at__isnull=False)

        order_id = request.query_params.get("order") or request.query_params.get(
            "order_id"
        )
        if order_id:
            queryset = queryset.filter(order_id=order_id)

        notification_type = request.query_params.get(
            "type"
        ) or request.query_params.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OrderNotificationSerializer(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = OrderNotificationSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Notifications"],
        summary="Get unread notification count",
        responses={200: NotificationUnreadCountSerializer},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="notifications/unread-count",
    )
    def notification_unread_count(self, request):
        unread_count = OrderNotification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
        ).count()

        return Response(
            {"unread_count": unread_count},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Order Notifications"],
        summary="Mark notification as read",
        responses={
            200: OrderNotificationSerializer,
            404: DetailResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path=r"notifications/(?P<notification_id>[^/.]+)/mark-read",
    )
    def mark_notification_read(self, request, notification_id=None):
        notification = get_object_or_404(
            OrderNotification.objects.select_related(
                "order",
                "actor",
                "recipient",
                "activity_log",
            ),
            pk=notification_id,
            recipient=request.user,
        )

        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])

        serializer = OrderNotificationSerializer(
            notification,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Notifications"],
        summary="Mark all current user's notifications as read",
        responses={200: MarkAllNotificationsReadResponseSerializer},
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="notifications/mark-all-read",
    )
    def mark_all_notifications_read(self, request):
        now = timezone.now()

        updated_count = OrderNotification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
        ).update(read_at=now)

        return Response(
            {
                "updated_count": updated_count,
                "read_at": now,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Order Comments"],
        summary="List order comments as threads",
        description="Returns root comments with nested replies.",
        responses={200: OrderCommentThreadSerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="comment-threads",
    )
    def comment_threads(self, request, pk=None):
        order = self.get_object()

        comments = (
            order.comments.select_related(
                "sender",
                "resolved_by",
                "parent",
                "parent__sender",
            )
            .prefetch_related(
                "replies",
                "replies__sender",
                "replies__resolved_by",
            )
            .filter(parent__isnull=True)
            .exclude(status=OrderComment.Status.DELETED)
            .order_by("created_at")
        )

        serializer = OrderCommentThreadSerializer(
            comments,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Comments"],
        summary="Resolve an order comment",
        description="Marks a comment as resolved and stores resolver user and timestamp.",
        responses={
            200: OrderCommentSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"comments/(?P<comment_id>[^/.]+)/resolve",
    )
    def resolve_comment(self, request, pk=None, comment_id=None):
        order = self.get_object()
        comment = self._get_order_comment(order, comment_id)

        if comment.status == OrderComment.Status.DELETED:
            return Response(
                {"detail": "Deleted comments cannot be resolved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if comment.resolved_at is not None:
            serializer = OrderCommentSerializer(
                comment,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        comment.resolved_by = request.user
        comment.resolved_at = timezone.now()
        comment.save(
            update_fields=[
                "resolved_by",
                "resolved_at",
                "updated_at",
            ]
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.COMMENT_RESOLVED,
            message="Comment resolved.",
            metadata={
                "comment_id": comment.id,
                "parent_id": comment.parent_id,
                "is_reply": comment.parent_id is not None,
                "target_type": comment.target_type,
                "resolved_by": request.user.id,
            },
        )

        serializer = OrderCommentSerializer(
            comment,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Comments"],
        summary="Unresolve an order comment",
        description="Clears resolved_by and resolved_at fields.",
        responses={
            200: OrderCommentSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"comments/(?P<comment_id>[^/.]+)/unresolve",
    )
    def unresolve_comment(self, request, pk=None, comment_id=None):
        order = self.get_object()
        comment = self._get_order_comment(order, comment_id)

        if comment.status == OrderComment.Status.DELETED:
            return Response(
                {"detail": "Deleted comments cannot be unresolved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if comment.resolved_at is None:
            serializer = OrderCommentSerializer(
                comment,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        previous_resolved_by_id = comment.resolved_by_id

        comment.resolved_by = None
        comment.resolved_at = None
        comment.save(
            update_fields=[
                "resolved_by",
                "resolved_at",
                "updated_at",
            ]
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.COMMENT_UNRESOLVED,
            message="Comment unresolved.",
            metadata={
                "comment_id": comment.id,
                "parent_id": comment.parent_id,
                "is_reply": comment.parent_id is not None,
                "target_type": comment.target_type,
                "previous_resolved_by": previous_resolved_by_id,
                "unresolved_by": request.user.id,
            },
        )

        serializer = OrderCommentSerializer(
            comment,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Dashboard"],
        summary="Get order dashboard summary",
        description="Returns high-level order counters for dashboard widgets.",
        parameters=[
            OpenApiParameter(
                "client", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "editor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "status", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "due_soon_days",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: DashboardSummarySerializer},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="dashboard-summary",
    )
    def dashboard_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        now = timezone.now()
        due_soon_days = self._parse_positive_int_query_param(
            request.query_params.get("due_soon_days"),
            "due_soon_days",
            default=7,
        )
        due_soon_until = now + timedelta(days=due_soon_days)

        total_orders = queryset.count()

        closed_orders = queryset.filter(status="closed").count()

        open_orders = queryset.exclude(status="closed").count()

        unassigned_orders = queryset.filter(editor__isnull=True).count()

        overdue_orders = (
            queryset.filter(
                deadline__lt=now,
            )
            .exclude(
                status="closed",
            )
            .count()
        )

        due_soon_orders = (
            queryset.filter(
                deadline__gte=now,
                deadline__lte=due_soon_until,
            )
            .exclude(
                status="closed",
            )
            .count()
        )

        settlement_pending_orders = queryset.filter(
            status="settlement_pending",
        ).count()

        paid_orders = queryset.filter(
            status="paid",
        ).count()

        return Response(
            {
                "total_orders": total_orders,
                "open_orders": open_orders,
                "closed_orders": closed_orders,
                "unassigned_orders": unassigned_orders,
                "overdue_orders": overdue_orders,
                "due_soon_orders": due_soon_orders,
                "due_soon_days": due_soon_days,
                "settlement_pending_orders": settlement_pending_orders,
                "paid_orders": paid_orders,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Order Dashboard"],
        summary="Get deadline summary",
        parameters=[
            OpenApiParameter(
                "due_soon_days",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: DeadlineSummarySerializer},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="deadline-summary",
    )
    def deadline_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        now = timezone.now()

        today_start = timezone.make_aware(
            datetime.combine(timezone.localdate(), time.min),
            timezone.get_current_timezone(),
        )
        today_end = timezone.make_aware(
            datetime.combine(timezone.localdate(), time.max),
            timezone.get_current_timezone(),
        )

        next_3_days = now + timedelta(days=3)
        next_7_days = now + timedelta(days=7)

        active_queryset = queryset.exclude(status="closed")

        overdue = active_queryset.filter(deadline__lt=now).count()

        due_today = active_queryset.filter(
            deadline__gte=today_start,
            deadline__lte=today_end,
        ).count()

        due_next_3_days = active_queryset.filter(
            deadline__gte=now,
            deadline__lte=next_3_days,
        ).count()

        due_next_7_days = active_queryset.filter(
            deadline__gte=now,
            deadline__lte=next_7_days,
        ).count()

        return Response(
            {
                "overdue": overdue,
                "due_today": due_today,
                "due_next_3_days": due_next_3_days,
                "due_next_7_days": due_next_7_days,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Order Dashboard"],
        summary="Get settlement pipeline summary",
        parameters=[
            OpenApiParameter(
                "client", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "editor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={200: SettlementSummarySerializer},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="settlement-summary",
    )
    def settlement_summary(self, request):
        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can view settlement summary.")

        queryset = self.filter_queryset(self.get_queryset())

        completed_orders = queryset.filter(status="completed").count()
        settlement_pending_orders = queryset.filter(status="settlement_pending").count()
        paid_orders = queryset.filter(status="paid").count()
        closed_orders = queryset.filter(status="closed").count()

        settlement_pipeline_total = queryset.filter(
            status__in=[
                "completed",
                "settlement_pending",
                "paid",
                "closed",
            ],
        ).count()

        return Response(
            {
                "completed_orders": completed_orders,
                "settlement_pending_orders": settlement_pending_orders,
                "paid_orders": paid_orders,
                "closed_orders": closed_orders,
                "settlement_pipeline_total": settlement_pipeline_total,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Order Dashboard"],
        summary="Get editor workload summary",
        description="Staff-only endpoint. Returns order workload grouped by editor.",
        parameters=[
            OpenApiParameter(
                "editor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={
            200: EditorWorkloadItemSerializer(many=True),
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="editor-workload",
    )
    def editor_workload(self, request):
        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can view editor workload.")

        queryset = self.filter_queryset(self.get_queryset())

        workload = (
            queryset.filter(editor__isnull=False)
            .values(
                "editor_id",
                "editor__username",
            )
            .annotate(
                total_orders=models.Count("id"),
                active_orders=models.Count(
                    "id",
                    filter=~models.Q(status="closed"),
                ),
                closed_orders=models.Count(
                    "id",
                    filter=models.Q(status="closed"),
                ),
                delivered_orders=models.Count(
                    "id",
                    filter=models.Q(status="delivered"),
                ),
                in_progress_orders=models.Count(
                    "id",
                    filter=models.Q(status="in_progress"),
                ),
                revision_required_orders=models.Count(
                    "id",
                    filter=models.Q(status="revision_required"),
                ),
            )
            .order_by("editor__username")
        )

        results = [
            {
                "editor": item["editor_id"],
                "editor_username": item["editor__username"],
                "total_orders": item["total_orders"],
                "active_orders": item["active_orders"],
                "closed_orders": item["closed_orders"],
                "delivered_orders": item["delivered_orders"],
                "in_progress_orders": item["in_progress_orders"],
                "revision_required_orders": item["revision_required_orders"],
            }
            for item in workload
        ]

        return Response(results, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Activity Logs"],
        summary="List order activity log",
        description="Returns audit trail for a specific order.",
        responses={200: OrderActivityLogSerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="activity-log",
    )
    def activity_log(self, request, pk=None):
        order = self.get_object()
        serializer = OrderActivityLogSerializer(order.activity_logs.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Activity Logs"],
        summary="List order status history",
        responses={200: OrderStatusHistorySerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="status-history",
    )
    def status_history(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusHistorySerializer(order.status_history.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Move completed order to settlement pending",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="start-settlement",
    )
    def start_settlement(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can start settlement.")

        if order.status != Order.Status.COMPLETED:
            return Response(
                {"detail": "Only completed orders can move to settlement pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = request.data.get("note", "").strip()

        self._update_order_status(
            order=order,
            new_status=Order.Status.SETTLEMENT_PENDING,
            user=request.user,
            note=note,
            extra_updates={
                "settlement_started_at": timezone.now(),
            },
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.SETTLEMENT_STARTED,
            message="Settlement process started.",
            metadata={
                "note": note,
            },
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Mark settlement as paid",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="mark-paid",
    )
    def mark_paid(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can mark orders as paid.")

        if order.status != Order.Status.SETTLEMENT_PENDING:
            return Response(
                {"detail": "Only settlement pending orders can be marked as paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = request.data.get("note", "").strip()

        self._update_order_status(
            order=order,
            new_status=Order.Status.PAID,
            user=request.user,
            note=note,
            extra_updates={
                "paid_at": timezone.now(),
            },
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.PAYMENT_RECORDED,
            message="Order marked as paid.",
            metadata={
                "note": note,
            },
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Close paid order",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="close",
    )
    def close_order(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can close orders.")

        if order.status != Order.Status.PAID:
            return Response(
                {"detail": "Only paid orders can be closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = request.data.get("note", "").strip()

        self._update_order_status(
            order=order,
            new_status=Order.Status.CLOSED,
            user=request.user,
            note=note,
            extra_updates={
                "closed_at": timezone.now(),
            },
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.ORDER_CLOSED,
            message="Order closed.",
            metadata={
                "note": note,
            },
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Supervisor rates order",
        request=RatingRequestSerializer,
        responses={
            200: OrderRatingSerializer,
            201: OrderRatingSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="supervisor-rate",
    )
    def supervisor_rate(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can rate as supervisor.")

        serializer = OrderRatingSerializer(data=request.data)

        if serializer.is_valid():
            self._save_or_update_rating(
                order=order,
                user=request.user,
                source=OrderRating.Source.SUPERVISOR,
                serializer=serializer,
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Client rates order",
        request=RatingRequestSerializer,
        responses={
            200: OrderRatingSerializer,
            201: OrderRatingSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="client-rate",
    )
    def client_rate(self, request, pk=None):
        order = self.get_object()

        if order.client_id != request.user.id:
            raise PermissionDenied("Only the order owner can rate this order.")

        serializer = OrderRatingSerializer(data=request.data)

        if serializer.is_valid():
            self._save_or_update_rating(
                order=order,
                user=request.user,
                source=OrderRating.Source.CLIENT,
                serializer=serializer,
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        methods=["GET"],
        tags=["Order Comments"],
        summary="List order comments",
        description="Returns flat list of comments for an order. Supports filters for resolved state, annotation, target type and target object.",
        parameters=[
            OpenApiParameter(
                "resolved", OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "has_annotation",
                OpenApiTypes.BOOL,
                OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "annotation_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "target_type", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "image", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "image_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "delivery", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "delivery_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "revision", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "revision_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={200: OrderCommentSerializer(many=True)},
    )
    @extend_schema(
        methods=["POST"],
        tags=["Order Comments"],
        summary="Create order comment or reply",
        description="Creates a root comment or a reply. Replies inherit target fields from their parent comment unless explicitly provided.",
        request=CommentCreateRequestSerializer,
        responses={
            201: OrderCommentSerializer,
            400: DetailResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Root order comment",
                value={
                    "target_type": "order",
                    "text": "Please review this order.",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Reply comment",
                value={
                    "parent": 7,
                    "text": "This is a reply.",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Point annotation",
                value={
                    "target_type": "delivery",
                    "delivery": 1,
                    "text": "Reduce smoothing here.",
                    "x": 42.5,
                    "y": 58.3,
                    "annotation_type": "point",
                    "annotation_label": "Skin smoothing",
                    "annotation_color": "#ff0000",
                    "annotation_data": {"priority": "high"},
                },
                request_only=True,
            ),
        ],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
    )
    def comments(self, request, pk=None):
        order = self.get_object()

        if request.method == "GET":
            comments = (
                order.comments.select_related(
                    "sender",
                    "resolved_by",
                    "parent",
                    "parent__sender",
                )
                .exclude(status=OrderComment.Status.DELETED)
                .order_by("created_at")
            )

            resolved_param = request.query_params.get("resolved")
            resolved = self._parse_bool_query_param(resolved_param)

            if resolved is True:
                comments = comments.filter(resolved_at__isnull=False)

            if resolved is False:
                comments = comments.filter(resolved_at__isnull=True)

            has_annotation_param = request.query_params.get("has_annotation")
            has_annotation = self._parse_bool_query_param(has_annotation_param)

            if has_annotation is True:
                comments = comments.exclude(annotation_type="none")

            if has_annotation is False:
                comments = comments.filter(annotation_type="none")

            annotation_type = request.query_params.get("annotation_type")
            if annotation_type:
                comments = comments.filter(annotation_type=annotation_type)

            target_type = request.query_params.get("target_type")
            if target_type:
                comments = comments.filter(target_type=target_type)

            image_id = request.query_params.get("image") or request.query_params.get(
                "image_id"
            )
            if image_id:
                comments = comments.filter(image_id=image_id)

            delivery_id = request.query_params.get(
                "delivery"
            ) or request.query_params.get("delivery_id")
            if delivery_id:
                comments = comments.filter(delivery_id=delivery_id)

            revision_id = request.query_params.get(
                "revision"
            ) or request.query_params.get("revision_id")
            if revision_id:
                comments = comments.filter(revision_id=revision_id)

            serializer = OrderCommentSerializer(
                comments,
                many=True,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        data = request.data.copy()
        parent_id = data.get("parent")

        if parent_id:
            try:
                parent_comment = order.comments.get(id=parent_id)
            except OrderComment.DoesNotExist:
                return Response(
                    {"parent": "Parent comment not found for this order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if parent_comment.status == OrderComment.Status.DELETED:
                return Response(
                    {"parent": "Cannot reply to a deleted comment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data["target_type"] = parent_comment.target_type
            data["image"] = parent_comment.image_id
            data["delivery"] = parent_comment.delivery_id
            data["revision"] = parent_comment.revision_id

        serializer = OrderCommentSerializer(
            data=request.data,
            context={
                "request": request,
                "order": order,
            },
        )

        if serializer.is_valid():
            comment = serializer.save(
                order=order,
                sender=request.user,
            )

            self._log_activity(
                order=order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.COMMENT_CREATED,
                message=(
                    "Comment reply created."
                    if comment.parent_id
                    else "Comment created."
                ),
                metadata={
                    "comment_id": comment.id,
                    "parent_id": comment.parent_id,
                    "is_reply": comment.parent_id is not None,
                    "target_type": comment.target_type,
                    "status": comment.status,
                    "annotation_type": comment.annotation_type,
                    "has_annotation": comment.annotation_type != "none",
                    "annotation_label": comment.annotation_label,
                },
            )

            output_serializer = OrderCommentSerializer(
                comment,
                context={"request": request},
            )
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        methods=["GET"],
        tags=["Order Comments"],
        summary="Retrieve a single order comment",
        responses={
            200: OrderCommentSerializer,
            404: DetailResponseSerializer,
        },
    )
    @extend_schema(
        methods=["PATCH", "PUT"],
        tags=["Order Comments"],
        summary="Update an order comment",
        request=CommentUpdateRequestSerializer,
        responses={
            200: OrderCommentSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    @extend_schema(
        methods=["DELETE"],
        tags=["Order Comments"],
        summary="Delete an order comment",
        description="Soft-deletes or deletes a comment depending on project implementation.",
        responses={
            204: None,
            404: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"comments/(?P<comment_id>[^/.]+)",
    )
    def comment_detail(self, request, pk=None, comment_id=None):
        order = self.get_object()

        try:
            comment = order.comments.get(id=comment_id)
        except OrderComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "PATCH":
            if comment.sender_id != request.user.id:
                raise PermissionDenied("Only the sender can edit this comment.")

            if comment.status == OrderComment.Status.DELETED:
                return Response(
                    {"detail": "Deleted comments cannot be edited."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            text = request.data.get("text")

            if text is None:
                return Response(
                    {"detail": "Text is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not str(text).strip():
                return Response(
                    {"detail": "Text cannot be empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            comment.text = str(text).strip()
            comment.is_edited = True
            comment.edited_at = timezone.now()
            comment.save(
                update_fields=[
                    "text",
                    "is_edited",
                    "edited_at",
                    "updated_at",
                ]
            )

            self._log_activity(
                order=comment.order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.COMMENT_UPDATED,
                message="Comment updated.",
                metadata={
                    "comment_id": comment.id,
                    "parent_id": comment.parent_id,
                    "is_reply": comment.parent_id is not None,
                    "target_type": comment.target_type,
                    "status": comment.status,
                },
            )

            serializer = OrderCommentSerializer(
                comment,
                data=request.data,
                partial=True,
                context={
                    "request": request,
                    "order": order,
                },
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "DELETE":
            if comment.sender_id != request.user.id and not self._is_staff_role(
                request.user
            ):
                raise PermissionDenied(
                    "Only the sender or staff can delete this comment."
                )

            if comment.status == OrderComment.Status.DELETED:
                return Response(
                    {"detail": "Comment is already deleted."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            comment.status = OrderComment.Status.DELETED
            comment.text = ""
            comment.deleted_at = timezone.now()
            comment.save(
                update_fields=[
                    "status",
                    "text",
                    "deleted_at",
                    "updated_at",
                ]
            )

            self._log_activity(
                order=comment.order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.COMMENT_DELETED,
                message="Comment deleted.",
                metadata={
                    "comment_id": comment.id,
                    "parent_id": comment.parent_id,
                    "is_reply": comment.parent_id is not None,
                    "target_type": comment.target_type,
                    "status": comment.status,
                },
            )

            return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Editor uploads delivery file",
        request=DeliveryUploadRequestSerializer,
        responses={
            201: OrderDeliverySerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="deliver",
        parser_classes=[MultiPartParser, FormParser],
    )
    def deliver(self, request, pk=None):
        order = self.get_object()

        if order.editor_id != request.user.id:
            raise PermissionDenied("Only the assigned editor can deliver this order.")

        if order.status != Order.Status.IN_PROGRESS:
            return Response(
                {"detail": "Only orders in progress can be delivered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderDeliverySerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save(
                order=order,
                uploaded_by=request.user,
            )

            self._update_order_status(
                order=order,
                new_status=Order.Status.DELIVERED,
                user=request.user,
                note=serializer.validated_data.get("note", "Editor delivered files."),
            )

            self._log_activity(
                order=order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.DELIVERY_UPLOADED,
                message="Editor uploaded delivery files.",
                metadata={
                    "delivery_id": delivery.id,
                    "note": delivery.note,
                },
            )

            order_serializer = self.get_serializer(order)
            return Response(
                order_serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Order Comments"],
        summary="Set order comment status",
        request=CommentStatusRequestSerializer,
        responses={
            200: OrderCommentSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Approve comment",
                value={"status": "approved"},
                request_only=True,
            ),
            OpenApiExample(
                "Reject comment",
                value={"status": "rejected"},
                request_only=True,
            ),
        ],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"comments/(?P<comment_id>[^/.]+)/set-status",
    )
    def comment_set_status(self, request, pk=None, comment_id=None):
        order = self.get_object()

        try:
            comment = order.comments.get(id=comment_id)
        except OrderComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if comment.sender_id != request.user.id and not self._is_staff_role(
            request.user
        ):
            raise PermissionDenied(
                "Only the sender or staff can change comment status."
            )

        new_status = request.data.get("status")

        valid_statuses = [
            OrderComment.Status.ACTIVE,
            OrderComment.Status.RESOLVED,
            OrderComment.Status.APPROVED,
            OrderComment.Status.DELETED,
        ]

        if new_status not in valid_statuses:
            return Response(
                {
                    "detail": "Invalid status.",
                    "valid_statuses": valid_statuses,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_status == OrderComment.Status.DELETED:
            comment.text = ""
            comment.deleted_at = timezone.now()

        comment.status = new_status
        comment.save(
            update_fields=[
                "status",
                "text",
                "deleted_at",
                "updated_at",
            ]
        )

        serializer = OrderCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Editor starts revision work",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="start-revision",
    )
    def start_revision(self, request, pk=None):
        order = self.get_object()

        if order.editor_id != request.user.id:
            raise PermissionDenied("Only the assigned editor can start revision work.")

        if order.status != Order.Status.REVISION_REQUIRED:
            return Response(
                {
                    "detail": "Only orders requiring revision can be started for revision."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        self._update_order_status(
            order=order,
            new_status=Order.Status.IN_PROGRESS,
            user=request.user,
            note="Editor started revision work.",
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.EDITOR_REVISION_STARTED,
            message="Editor started revision work.",
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Client approves order",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="client-approve",
    )
    def client_approve(self, request, pk=None):
        order = self.get_object()

        if order.client_id != request.user.id:
            raise PermissionDenied("Only the order owner can approve this order.")

        if order.status != Order.Status.CLIENT_REVIEW:
            return Response(
                {"detail": "Only orders in client review can be approved by client."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self._update_order_status(
            order=order,
            new_status=Order.Status.COMPLETED,
            user=request.user,
            note="Client approved the order.",
            extra_updates={
                "client_approved_at": timezone.now(),
            },
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.CLIENT_APPROVED,
            message="Client approved the order.",
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Client requests revision",
        request=NoteRequestSerializer,
        responses={
            201: OrderRevisionSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="client-request-revision",
    )
    def client_request_revision(self, request, pk=None):
        order = self.get_object()

        if order.client_id != request.user.id:
            raise PermissionDenied("Only the order owner can request client revision.")

        if order.status != Order.Status.CLIENT_REVIEW:
            return Response(
                {
                    "detail": "Only orders in client review can receive client revision requests."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderRevisionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                order=order,
                requested_by=request.user,
                source=OrderRevision.Source.CLIENT,
            )

            self._update_order_status(
                order=order,
                new_status=Order.Status.CLIENT_REVISION_REQUESTED,
                user=request.user,
                note=serializer.validated_data["note"],
            )

            self._log_activity(
                order=order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.CLIENT_REVISION_REQUESTED,
                message="Client requested revision.",
                metadata={
                    "revision_id": revision.id,
                    "note": revision.note,
                },
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Supervisor accepts client revision request",
        request=NoteRequestSerializer,
        responses={
            200: OrderRevisionSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="supervisor-accept-client-revision",
    )
    def supervisor_accept_client_revision(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied(
                "Only staff roles can accept client revision requests."
            )

        if order.status != Order.Status.CLIENT_REVISION_REQUESTED:
            return Response(
                {
                    "detail": "Only client revision requested orders can be accepted by supervisor."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        latest_client_revision = (
            order.revisions.filter(source=OrderRevision.Source.CLIENT)
            .order_by("-created_at")
            .first()
        )

        note = request.data.get("note", "").strip()

        if note:
            OrderComment.objects.create(
                order=order,
                sender=request.user,
                target_type=OrderComment.TargetType.REVISION,
                revision=latest_client_revision,
                text=note,
            )

        self._update_order_status(
            order=order,
            new_status=Order.Status.REVISION_REQUIRED,
            user=request.user,
            note=note or "Supervisor accepted client revision request.",
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.SUPERVISOR_ACCEPTED_CLIENT_REVISION,
            message="Supervisor accepted client revision request.",
            metadata={
                "note": note,
                "revision_id": (
                    latest_client_revision.id if latest_client_revision else None
                ),
            },
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Supervisor rejects client revision request",
        request=NoteRequestSerializer,
        responses={
            200: OrderRevisionSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="supervisor-reject-client-revision",
    )
    def supervisor_reject_client_revision(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied(
                "Only staff roles can reject client revision requests."
            )

        if order.status != Order.Status.CLIENT_REVISION_REQUESTED:
            return Response(
                {
                    "detail": "Only client revision requested orders can be rejected by supervisor."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        latest_client_revision = (
            order.revisions.filter(source=OrderRevision.Source.CLIENT)
            .order_by("-created_at")
            .first()
        )

        note = request.data.get("note", "").strip()

        if note:
            OrderComment.objects.create(
                order=order,
                sender=request.user,
                target_type=OrderComment.TargetType.REVISION,
                revision=latest_client_revision,
                text=note,
            )

        self._update_order_status(
            order=order,
            new_status=Order.Status.CLIENT_REVIEW,
            user=request.user,
            note=note or "Supervisor rejected client revision request.",
        )

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.SUPERVISOR_REJECTED_CLIENT_REVISION,
            message="Supervisor rejected client revision request.",
            metadata={
                "note": note,
                "revision_id": (
                    latest_client_revision.id if latest_client_revision else None
                ),
            },
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Editor starts work on assigned order",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="start-work",
    )
    def start_work(self, request, pk=None):
        order = self.get_object()

        if order.editor_id != request.user.id:
            raise PermissionDenied("Only the assigned editor can start this order.")

        if order.status != Order.Status.ASSIGNED:
            return Response(
                {"detail": "Only assigned orders can be started."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.IN_PROGRESS
        order.save(update_fields=["status", "updated_at"])

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.WORK_STARTED,
            message="Editor started work on the order.",
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Assign editor to order",
        request=AssignEditorRequestSerializer,
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="assign-editor",
    )
    def assign_editor(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can assign editors.")

        if order.status != Order.Status.IN_REVIEW:
            return Response(
                {"detail": "Only orders in review can be assigned to an editor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        editor_id = request.data.get("editor_id")

        if not editor_id:
            return Response(
                {"detail": "editor_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            editor = User.objects.get(id=editor_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Editor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if getattr(editor, "role", None) != "editor":
            return Response(
                {"detail": "Selected user is not an editor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.editor = editor
        order.status = Order.Status.ASSIGNED
        order.save(update_fields=["editor", "status", "updated_at"])

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.EDITOR_ASSIGNED,
            message="Editor assigned to the order.",
            metadata={
                "editor_id": order.editor_id,
                "editor_username": getattr(order.editor, "username", ""),
            },
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _is_staff_role(self, user):
        return user.is_staff or getattr(user, "role", None) in [
            "admin",
            "support",
            "supervisor",
        ]

    def get_queryset(self):
        queryset = Order.objects.select_related("client", "editor")

        user = self.request.user

        if not self._is_staff_role(user):
            queryset = queryset.filter(models.Q(client=user) | models.Q(editor=user))

        if getattr(self, "action", None) != "list":
            queryset = queryset.prefetch_related(
                "images",
                "deliveries",
                "revisions",
                "ratings",
                "comments",
                "status_history",
                "activity_logs",
                "comments__replies",
            )

        return self._apply_order_filters(queryset)

    def perform_create(self, serializer):
        if getattr(self.request.user, "role", None) != "client":
            raise PermissionDenied("Only clients can create orders.")

        serializer.save(client=self.request.user)

    def perform_destroy(self, instance):
        raise PermissionDenied("Deleting orders is not allowed.")

    @extend_schema(
        tags=["Order Workflow"],
        summary="Supervisor approves delivered order",
        request=RatingRequestSerializer,
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="supervisor-approve",
    )
    def supervisor_approve(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can approve delivered orders.")

        if order.status != Order.Status.DELIVERED:
            return Response(
                {"detail": "Only delivered orders can be approved by supervisor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderRatingSerializer(data=request.data)

        if serializer.is_valid():
            self._save_or_update_rating(
                order=order,
                user=request.user,
                source=OrderRating.Source.SUPERVISOR,
                serializer=serializer,
            )

            self._log_activity(
                order=order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.SUPERVISOR_APPROVED,
                message="Supervisor approved the order.",
                metadata={
                    "rating_id": rating.id,
                    "score": rating.score,
                    "comment": rating.comment,
                },
            )

            self._log_activity(
                order=order,
                actor=request.user,
                activity_type=(
                    OrderActivityLog.ActivityType.RATING_CREATED
                    if created
                    else OrderActivityLog.ActivityType.RATING_UPDATED
                ),
                message="Order rating saved.",
                metadata={
                    "rating_id": rating.id,
                    "source": rating.source,
                    "score": rating.score,
                    "comment": rating.comment,
                },
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Supervisor requests revision from editor",
        request=NoteRequestSerializer,
        responses={
            201: OrderRevisionSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="supervisor-request-revision",
    )
    def supervisor_request_revision(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can request revisions.")

        if order.status != Order.Status.DELIVERED:
            return Response(
                {
                    "detail": "Only delivered orders can have supervisor revision requests."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderRevisionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                order=order,
                requested_by=request.user,
                source=OrderRevision.Source.SUPERVISOR,
            )

            self._update_order_status(
                order=order,
                new_status=Order.Status.REVISION_REQUIRED,
                user=request.user,
                note=serializer.validated_data["note"],
                extra_updates={
                    "revision_count": order.revision_count + 1,
                },
            )

            self._log_activity(
                order=order,
                actor=request.user,
                activity_type=OrderActivityLog.ActivityType.SUPERVISOR_REVISION_REQUESTED,
                message="Supervisor requested revision.",
                metadata={
                    "revision_id": revision.id,
                    "note": revision.note,
                },
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Start supervisor review",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="start-review",
    )
    def start_review(self, request, pk=None):
        order = self.get_object()

        if not self._is_staff_role(request.user):
            raise PermissionDenied("Only staff roles can start order review.")

        if order.status != Order.Status.SUBMITTED:
            return Response(
                {"detail": "Only submitted orders can be moved to review."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.IN_REVIEW
        order.save(update_fields=["status", "updated_at"])

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.REVIEW_STARTED,
            message="Order moved to review stage.",
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Submit draft order",
        responses={
            200: OrderSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="submit",
    )
    def submit(self, request, pk=None):
        order = self.get_object()

        if order.client_id != request.user.id:
            raise PermissionDenied("Only the order owner can submit this order.")

        if order.status != Order.Status.DRAFT:
            return Response(
                {"detail": "Only draft orders can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not order.images.exists():
            return Response(
                {
                    "detail": "At least one image is required before submitting the order."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.SUBMITTED
        order.save(update_fields=["status", "updated_at"])

        self._log_activity(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.ORDER_SUBMITTED,
            message="Order submitted for review.",
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Order Workflow"],
        summary="Upload original image for order",
        request=ImageUploadRequestSerializer,
        responses={
            201: OrderImageSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="upload-image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        order = self.get_object()

        serializer = OrderImageSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save(order=order)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
