from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import GenericViewSet
from .sla_models import DeliveryPenalty, SLAConfig
from .sla_serializers import (
    DeliveryPenaltySerializer,
    PenaltyApplySerializer,
    PenaltyWaiveSerializer,
    SLAConfigSerializer,
)
from .sla_handler import SLAHandler


class DeliveryPenaltyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """ViewSet for managing delivery penalties."""

    serializer_class = DeliveryPenaltySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DeliveryPenalty.objects.select_related('order', 'editor').all()
        return DeliveryPenalty.objects.select_related('order', 'editor').filter(editor=user)

    def get_serializer_class(self):
        if self.action == 'apply':
            return PenaltyApplySerializer
        elif self.action == 'waive':
            return PenaltyWaiveSerializer
        return DeliveryPenaltySerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def apply(self, request, pk=None):
        penalty = self.get_object()

        if penalty.status != DeliveryPenalty.Status.PENDING:
            return Response(
                {'error': f'Cannot apply penalty with status: {penalty.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PenaltyApplySerializer(
            data=request.data,
            context={'penalty': penalty, 'request': request}
        )

        if serializer.is_valid():
            penalty = serializer.save()
            return Response(DeliveryPenaltySerializer(penalty).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def waive(self, request, pk=None):
        penalty = self.get_object()

        if penalty.status != DeliveryPenalty.Status.PENDING:
            return Response(
                {'error': f'Cannot waive penalty with status: {penalty.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PenaltyWaiveSerializer(
            data=request.data,
            context={'penalty': penalty, 'request': request}
        )

        if serializer.is_valid():
            penalty = serializer.save()
            return Response(DeliveryPenaltySerializer(penalty).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser],
            url_path='check-all')  # ✅ dash بجای underscore
    def check_all(self, request):
        late_count = SLAHandler.check_all_late_orders()
        return Response({
            'message': f'SLA check complete. Created {late_count} new penalties.',
            'penalties_created': late_count,
        })


class SLAConfigViewSet(viewsets.ModelViewSet):
    queryset = SLAConfig.objects.all()
    serializer_class = SLAConfigSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']