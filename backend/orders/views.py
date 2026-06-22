from rest_framework import permissions, viewsets

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.role in ["admin", "support", "supervisor"]:
            return Order.objects.all()

        if user.role == "client":
            return Order.objects.filter(client=user)

        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)