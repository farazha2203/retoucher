"""
Serializers for SLA and penalty functionality.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .sla_models import DeliveryPenalty, SLAConfig


class DeliveryPenaltySerializer(serializers.ModelSerializer):
    order_title = serializers.SerializerMethodField()
    editor_name = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryPenalty
        fields = [
            'id', 'order', 'order_title', 'editor', 'editor_name',
            'penalty_type', 'status', 'order_amount', 'penalty_amount',
            'penalty_percent', 'deadline', 'delivered_at', 'days_late',
            'reason', 'admin_note', 'created_at', 'applied_at', 'waived_at',
        ]
        read_only_fields = [
            'id', 'penalty_amount', 'penalty_percent', 'days_late',
            'created_at', 'applied_at', 'waived_at',
        ]

    def get_order_title(self, obj):
        return obj.order.title

    def get_editor_name(self, obj):
        return obj.editor.get_full_name() or obj.editor.username


class PenaltyApplySerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)

    def save(self):
        penalty = self.context['penalty']
        request = self.context['request']
        note = self.validated_data.get('note', '')
        try:
            penalty.apply(applied_by=request.user, note=note)
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or {
                "detail": list(exc.messages)
            }
            raise serializers.ValidationError(detail) from exc
        return penalty


class PenaltyWaiveSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)

    def save(self):
        penalty = self.context['penalty']
        request = self.context['request']
        note = self.validated_data.get('note', '')
        try:
            penalty.waive(waived_by=request.user, note=note)
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or {
                "detail": list(exc.messages)
            }
            raise serializers.ValidationError(detail) from exc
        return penalty


class SLAConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAConfig
        fields = [
            'id', 'penalty_percent_per_day', 'max_penalty_percent',
            'grace_period_hours', 'is_active', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']