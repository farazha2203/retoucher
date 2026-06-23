from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Order,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderRating,
    OrderRevision,
)
from .permissions import CanCreateOrder, IsOrderOwnerOrStaffRole
from .serializers import (
    OrderDeliverySerializer,
    OrderImageSerializer,
    OrderRatingSerializer,
    OrderRevisionSerializer,
    OrderSerializer,
    OrderCommentSerializer,
)

User = get_user_model()


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanCreateOrder,
        IsOrderOwnerOrStaffRole,
    )

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

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
    )
    def comments(self, request, pk=None):
        order = self.get_object()

        if request.method == "GET":
            comments = order.comments.exclude(
                status=OrderComment.Status.DELETED,
            )
            serializer = OrderCommentSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = OrderCommentSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(
                order=order,
                sender=request.user,
            )

            output_serializer = OrderCommentSerializer(comment)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

            comment.text = text
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

            serializer = OrderCommentSerializer(comment)
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

            return Response(status=status.HTTP_204_NO_CONTENT)

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

            order.status = Order.Status.DELIVERED
            order.save(update_fields=["status", "updated_at"])

            order_serializer = self.get_serializer(order)
            return Response(
                order_serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
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

        if comment.sender_id != request.user.id and not self._is_staff_role(request.user):
            raise PermissionDenied("Only the sender or staff can change comment status.")

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

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _is_staff_role(self, user):
        return user.is_staff or getattr(user, "role", None) in [
            "admin",
            "support",
            "supervisor",
        ]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.role in ["admin", "support", "supervisor"]:
            return Order.objects.all()

        if user.role == "client":
            return Order.objects.filter(client=user)

        if user.role == "editor":
            return Order.objects.filter(editor=user)

        return Order.objects.none()

    def perform_create(self, serializer):
        if getattr(self.request.user, "role", None) != "client":
            raise PermissionDenied("Only clients can create orders.")

        serializer.save(client=self.request.user)

    def perform_destroy(self, instance):
        raise PermissionDenied("Deleting orders is not allowed.")

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

            order.supervisor_approved_at = timezone.now()
            order.status = Order.Status.CLIENT_REVIEW
            order.save(
                update_fields=[
                    "supervisor_approved_at",
                    "status",
                    "updated_at",
                ]
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

            order.revision_count += 1
            order.status = Order.Status.REVISION_REQUIRED
            order.save(
                update_fields=[
                    "revision_count",
                    "status",
                    "updated_at",
                ]
            )

            order_serializer = self.get_serializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
