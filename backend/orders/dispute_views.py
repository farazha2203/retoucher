"""
Views for dispute resolution.
"""
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import GenericViewSet
from django.shortcuts import get_object_or_404

from .models import Order
from .dispute_models import Dispute, DisputeMessage, DisputeEvidence
from .dispute_serializers import (
    DisputeSerializer,
    DisputeDetailSerializer,
    DisputeCreateSerializer,
    DisputeResolveSerializer,
    DisputeMessageCreateSerializer,
    DisputeMessageSerializer,
    DisputeEvidenceSerializer,
)


class DisputeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """ViewSet for managing disputes."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Dispute.objects.select_related('order', 'initiated_by').all()
        # Client or editor only sees disputes related to their orders
        return Dispute.objects.select_related('order', 'initiated_by').filter(
            order__client=user
        ) | Dispute.objects.select_related('order', 'initiated_by').filter(
            order__editor=user
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DisputeDetailSerializer
        return DisputeSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, methods=['post'])
    def open(self, request):
        """
        POST /api/orders/disputes/open/
        {
            "order_id": 1,
            "category": "quality",
            "description": "The work was not as described..."
        }
        """
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=order_id)

        # Only client or editor of the order can open dispute
        if request.user not in [order.client, order.editor] and not request.user.is_staff:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if dispute already exists
        if hasattr(order, 'dispute') and order.dispute:
            return Response({'error': 'A dispute already exists for this order.'}, status=status.HTTP_400_BAD_REQUEST)

        # Only completed/delivered orders can have disputes
        eligible_statuses = [
            Order.Status.COMPLETED,
            Order.Status.DELIVERED,
            Order.Status.CLIENT_REVIEW,
            Order.Status.CLOSED,
        ]
        if order.status not in eligible_statuses:
            return Response(
                {'error': f'Disputes can only be opened for completed orders. Current status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DisputeCreateSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )

        if serializer.is_valid():
            dispute = serializer.save()
            return Response(DisputeDetailSerializer(dispute, context={'request': request}).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        """
        POST /api/orders/disputes/{id}/resolve/
        {
            "resolution": "favors_client",
            "note": "Evidence shows quality was below standard",
            "refund_amount": 300000
        }
        """
        dispute = self.get_object()

        if dispute.status == Dispute.Status.RESOLVED:
            return Response({'error': 'Dispute already resolved.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DisputeResolveSerializer(
            data=request.data,
            context={'dispute': dispute, 'request': request}
        )

        if serializer.is_valid():
            dispute = serializer.save()
            return Response(DisputeDetailSerializer(dispute, context={'request': request}).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def message(self, request, pk=None):
        """
        POST /api/orders/disputes/{id}/message/
        {
            "message": "I have provided all work as agreed..."
        }
        """
        dispute = self.get_object()
        order = dispute.order

        # Only parties involved can send messages
        if request.user not in [order.client, order.editor] and not request.user.is_staff:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        if dispute.status == Dispute.Status.RESOLVED:
            return Response({'error': 'Cannot message in a resolved dispute.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DisputeMessageCreateSerializer(
            data=request.data,
            context={'dispute': dispute, 'request': request}
        )

        if serializer.is_valid():
            msg = serializer.save()
            return Response(DisputeMessageSerializer(msg).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_evidence(self, request, pk=None):
        """
        POST /api/orders/disputes/{id}/upload_evidence/
        """
        dispute = self.get_object()
        order = dispute.order

        if request.user not in [order.client, order.editor] and not request.user.is_staff:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        if dispute.status == Dispute.Status.RESOLVED:
            return Response({'error': 'Cannot upload evidence to a resolved dispute.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DisputeEvidenceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dispute=dispute, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)