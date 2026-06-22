from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Order
from .permissions import CanCreateOrder, IsOrderOwnerOrStaffRole
from .serializers import OrderImageSerializer, OrderSerializer

User = get_user_model()

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanCreateOrder,
        IsOrderOwnerOrStaffRole,
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
                {"detail": "At least one image is required before submitting the order."},
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