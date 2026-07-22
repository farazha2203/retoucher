"""
Serializers for refund functionality.
"""
from rest_framework import serializers
from .refund_models import Refund, RefundEvidence
from notifications.services import create_notification
from notifications.models import Notification
from django.utils import timezone


class RefundEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundEvidence
        fields = ['id', 'file', 'description', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class RefundSerializer(serializers.ModelSerializer):
    evidence = RefundEvidenceSerializer(many=True, read_only=True)
    client_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'order', 'reason', 'status', 'requested_amount',
            'approved_amount', 'description', 'admin_note', 'evidence',
            'requested_at', 'reviewed_at', 'processed_at', 'client_name'
        ]
        read_only_fields = [
            'id', 'status', 'approved_amount', 'admin_note',
            'requested_at', 'reviewed_at', 'processed_at'
        ]
    
    def get_client_name(self, obj):
        return obj.order.client.get_full_name() or obj.order.client.username


class RefundDetailSerializer(serializers.ModelSerializer):
    evidence = RefundEvidenceSerializer(many=True, read_only=True)
    order_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'order', 'order_detail', 'reason', 'status',
            'requested_amount', 'approved_amount', 'description',
            'admin_note', 'evidence', 'requested_by', 'reviewed_by',
            'requested_at', 'reviewed_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'status', 'requested_by', 'reviewed_by',
            'reviewed_at', 'processed_at'
        ]
    
    def get_order_detail(self, obj):
        return {
            'id': obj.order.id,
            'title': obj.order.title,
            'client': obj.order.client_id,
            'editor': obj.order.editor_id,
            'status': obj.order.status,
            'agreed_price': str(obj.order.agreed_price),  # ✅ FIXED
        }


class RefundApproveSerializer(serializers.Serializer):
    approved_amount = serializers.IntegerField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)
    
    def validate_approved_amount(self, value):
        refund = self.context['refund']
        if value > refund.requested_amount:
            raise serializers.ValidationError(
                "Approved amount cannot exceed requested amount."
            )
        if value <= 0:
            raise serializers.ValidationError(
                "Approved amount must be positive."
            )
        return value
    
    def save(self):
        refund = self.context['refund']
        request = self.context['request']
        
        amount = self.validated_data.get('approved_amount', refund.requested_amount)
        note = self.validated_data.get('note', '')
        
        refund.approve(amount=amount, reviewed_by=request.user, note=note)
        
        # Notify client
        try:
            create_notification(
                recipient=refund.order.client,
                notification_type=Notification.Type.PAYMENT,
                title="Refund approved",
                message=f"Your refund request for order {refund.order_id} has been approved.",
                data={
                    'refund_id': refund.id,
                    'order_id': refund.order_id,
                    'amount': amount,
                },
            )
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        return refund


class RefundRejectSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)
    
    def save(self):
        refund = self.context['refund']
        request = self.context['request']
        note = self.validated_data.get('note', '')
        
        refund.reject(reviewed_by=request.user, note=note)
        
        # Notify client
        try:
            create_notification(
                recipient=refund.order.client,
                notification_type=Notification.Type.PAYMENT,
                title="Refund rejected",
                message=f"Your refund request for order {refund.order_id} has been rejected.",
                priority=Notification.Priority.HIGH,
                data={
                    'refund_id': refund.id,
                    'order_id': refund.order_id,
                },
            )
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        return refund


class RefundRequestSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Refund.Reason.choices)
    description = serializers.CharField(required=False, allow_blank=True)
    requested_amount = serializers.IntegerField()
    
    def validate_requested_amount(self, value):
        order = self.context['order']
        if value <= 0 or value > int(order.agreed_price):  # ✅ FIXED
            raise serializers.ValidationError("Invalid refund amount.")
        return value
    
    def create(self, validated_data):
        order = self.context['order']
        request = self.context['request']
        
        # Check if refund already exists
        if hasattr(order, 'refund') and order.refund:
            raise serializers.ValidationError(
                "Refund already exists for this order."
            )
        
        refund = Refund.objects.create(
            order=order,
            reason=validated_data['reason'],
            description=validated_data.get('description', ''),
            requested_amount=validated_data['requested_amount'],
            requested_by=request.user,
        )
        
        # Notify admin
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                create_notification(
                    recipient=admin,
                    notification_type=Notification.Type.PAYMENT,
                    title="New refund request",
                    message=f"New refund request for order {order.id}.",
                    priority=Notification.Priority.HIGH,
                    data={
                        'refund_id': refund.id,
                        'order_id': order.id,
                        'amount': refund.requested_amount,
                    },
                )
        except Exception as e:
            print(f"Error creating admin notification: {e}")
        
        return refund