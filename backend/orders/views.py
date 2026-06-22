from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Order
from .permissions import CanCreateOrder, IsOrderOwnerOrStaffRole
from .serializers import OrderImageSerializer, OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanCreateOrder,
        IsOrderOwnerOrStaffRole,
    )

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.role in ["admin", "support", "supervisor"]:
            return Order.objects.all()

        if user.role == "client":
            return Order.objects.filter(client=user)

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