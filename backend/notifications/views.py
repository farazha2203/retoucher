from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("recipient", "actor")
            .order_by("-created_at", "-id")
        )

        is_read = self.request.query_params.get("is_read")
        notification_type = self.request.query_params.get("notification_type")
        priority = self.request.query_params.get("priority")

        if is_read is not None:
            normalized_is_read = is_read.lower()

            if normalized_is_read in ("true", "1", "yes"):
                queryset = queryset.filter(is_read=True)
            elif normalized_is_read in ("false", "0", "no"):
                queryset = queryset.filter(is_read=False)

        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset
    
    @action(detail=True, methods=["post"], url_path="mark-unread")
    def mark_unread(self, request, pk=None):
        notification = self.get_object()

        notification.is_read = False
        notification.read_at = None
        notification.save(update_fields=["is_read", "read_at"])

        serializer = self.get_serializer(notification)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="clear-read")
    def clear_read(self, request):
        deleted_count, _ = Notification.objects.filter(
            recipient=request.user,
            is_read=True,
        ).delete()

        return Response(
            {
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        queryset = Notification.objects.filter(recipient=request.user)

        total_count = queryset.count()
        unread_count = queryset.filter(is_read=False).count()
        read_count = total_count - unread_count
        high_priority_unread_count = queryset.filter(
            is_read=False,
            priority=Notification.Priority.HIGH,
        ).count()

        by_type = {
            choice_value: 0
            for choice_value, _ in Notification.Type.choices
        }

        for row in queryset.values("notification_type").annotate(count=Count("id")):
            by_type[row["notification_type"]] = row["count"]

        by_priority = {
            choice_value: 0
            for choice_value, _ in Notification.Priority.choices
        }

        for row in queryset.values("priority").annotate(count=Count("id")):
            by_priority[row["priority"]] = row["count"]

        return Response(
            {
                "total_count": total_count,
                "unread_count": unread_count,
                "read_count": read_count,
                "high_priority_unread_count": high_priority_unread_count,
                "by_type": by_type,
                "by_priority": by_priority,
            }
        )

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="mark-unread")
    def mark_unread(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_unread()

        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        unread_notifications = self.get_queryset().filter(is_read=False)
        updated_count = unread_notifications.count()

        unread_notifications.update(
            is_read=True,
            read_at=timezone.now(),
        )

        return Response(
            {"updated_count": updated_count},
            status=status.HTTP_200_OK,
        )