"""
Views for refund functionality.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from orders.models import Order
from .refund_models import Refund, RefundEvidence
from .refund_serializers import (
    RefundSerializer,
    RefundDetailSerializer,
    RefundEvidenceSerializer,
    RefundApproveSerializer,
    RefundRejectSerializer,
    RefundRequestSerializer,
)
from .refund_permissions import CanReviewRefund


class RefundViewSet(viewsets.ModelViewSet):
    """ViewSet for managing refunds."""

    queryset = Refund.objects.select_related('order', 'order__client', 'order__editor')
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Refund.objects.all()
        return Refund.objects.filter(order__client=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RefundDetailSerializer
        elif self.action == 'approve':
            return RefundApproveSerializer
        elif self.action == 'reject':
            return RefundRejectSerializer
        return RefundSerializer

    def create(self, request, *args, **kwargs):
        """
        POST /api/payments/refunds/
        {
            "order_id": 1,
            "reason": "dispute",
            "description": "...",
            "requested_amount": 400000
        }
        """
        order_id = request.data.get('order_id')
        if not order_id:
            return Response(
                {'error': 'order_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(Order, id=order_id)

        # Permission check
        if order.client != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to request refund for this order.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if refund already exists
        if Refund.objects.filter(order=order).exists():
            return Response(
                {'error': 'A refund request already exists for this order.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check order status
        eligible_statuses = [
            Order.Status.COMPLETED,
            Order.Status.CLOSED,
            Order.Status.PAID,
        ]
        if order.status not in eligible_statuses:
            return Response(
                {'error': f'Only completed or closed orders can be refunded. Current status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check 7-day window
        reference_date = order.closed_at or order.paid_at
        if reference_date:
            days_elapsed = (timezone.now() - reference_date).days
            if days_elapsed > 7:
                return Response(
                    {'error': 'Refund requests must be submitted within 7 days of order completion.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = RefundRequestSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )

        if serializer.is_valid():
            refund = serializer.save()
            return Response(
                RefundSerializer(refund).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanReviewRefund])
    def approve(self, request, pk=None):
        """POST /api/payments/refunds/{id}/approve/"""
        refund = self.get_object()

        if refund.status != Refund.Status.REQUESTED:
            return Response(
                {'error': f'Cannot approve refund with status: {refund.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefundApproveSerializer(
            data=request.data,
            context={'refund': refund, 'request': request}
        )

        if serializer.is_valid():
            refund = serializer.save()
            return Response(RefundDetailSerializer(refund).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanReviewRefund])
    def reject(self, request, pk=None):
        """POST /api/payments/refunds/{id}/reject/"""
        refund = self.get_object()

        if refund.status != Refund.Status.REQUESTED:
            return Response(
                {'error': f'Cannot reject refund with status: {refund.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefundRejectSerializer(
            data=request.data,
            context={'refund': refund, 'request': request}
        )

        if serializer.is_valid():
            refund = serializer.save()
            return Response(RefundDetailSerializer(refund).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefundEvidenceViewSet(viewsets.GenericViewSet):
    """ViewSet for managing refund evidence."""

    serializer_class = RefundEvidenceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        refund_id = self.kwargs.get('refund_pk')
        return RefundEvidence.objects.filter(refund_id=refund_id)

    def create(self, request, *args, **kwargs):
        """POST /api/payments/refunds/{refund_pk}/evidence/"""
        refund_id = self.kwargs.get('refund_pk')
        refund = get_object_or_404(Refund, id=refund_id)

        if refund.order.client != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(refund=refund, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        """GET /api/payments/refunds/{refund_pk}/evidence/"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)