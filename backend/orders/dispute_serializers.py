"""
Serializers for dispute resolution.
"""
from rest_framework import serializers
from .dispute_models import Dispute, DisputeMessage, DisputeEvidence
from notifications.services import create_notification
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta


class DisputeEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisputeEvidence
        fields = ['id', 'file', 'description', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class DisputeMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = DisputeMessage
        fields = ['id', 'sender', 'sender_name', 'message', 'created_at', 'is_admin_note']
        read_only_fields = ['id', 'sender', 'created_at']

    def get_sender_name(self, obj):
        if not obj.sender:
            return "System"
        return obj.sender.get_full_name() or obj.sender.username


class DisputeSerializer(serializers.ModelSerializer):
    initiated_by_name = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()

    class Meta:
        model = Dispute
        fields = [
            'id', 'order', 'category', 'description', 'status',
            'resolution', 'resolution_note', 'refund_amount',
            'initiated_by', 'initiated_by_name',
            'created_at', 'resolved_at', 'response_deadline',
            'message_count', 'evidence_count',
        ]
        read_only_fields = [
            'id', 'status', 'resolution', 'resolution_note',
            'resolved_at', 'initiated_by',
        ]

    def get_initiated_by_name(self, obj):
        if not obj.initiated_by:
            return None
        return obj.initiated_by.get_full_name() or obj.initiated_by.username

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_evidence_count(self, obj):
        return obj.evidence.count()


class DisputeDetailSerializer(DisputeSerializer):
    messages = serializers.SerializerMethodField()
    evidence = DisputeEvidenceSerializer(many=True, read_only=True)
    order_detail = serializers.SerializerMethodField()

    class Meta(DisputeSerializer.Meta):
        fields = DisputeSerializer.Meta.fields + ['messages', 'evidence', 'order_detail']

    def get_messages(self, obj):
        request = self.context.get('request')
        qs = obj.messages.all()
        # Non-admin users don't see admin notes
        if request and not request.user.is_staff:
            qs = qs.filter(is_admin_note=False)
        return DisputeMessageSerializer(qs, many=True).data

    def get_order_detail(self, obj):
        return {
            'id': obj.order.id,
            'title': obj.order.title,
            'client_id': obj.order.client_id,
            'editor_id': obj.order.editor_id,
            'status': obj.order.status,
            'agreed_price': str(obj.order.agreed_price),
        }


class DisputeCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=Dispute.Category.choices)
    description = serializers.CharField(min_length=20)

    def create(self, validated_data):
        order = self.context['order']
        request = self.context['request']

        dispute = Dispute.objects.create(
            order=order,
            initiated_by=request.user,
            category=validated_data['category'],
            description=validated_data['description'],
            response_deadline=timezone.now() + timedelta(hours=48),
        )

        # Notify both parties + admin
        other_user = order.editor if request.user == order.client else order.client
        try:
            create_notification(
                recipient=other_user,
                notification_type=Notification.Type.ORDER,
                title="Dispute opened",
                message=f"A dispute has been opened for order #{order.id}. Please respond within 48 hours.",
                priority=Notification.Priority.HIGH,
                data={'order_id': order.id, 'dispute_id': dispute.id},
            )
        except Exception:
            pass

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for admin in User.objects.filter(is_staff=True):
                create_notification(
                    recipient=admin,
                    notification_type=Notification.Type.ORDER,
                    title="New dispute opened",
                    message=f"New dispute for order #{order.id}.",
                    priority=Notification.Priority.HIGH,
                    data={'order_id': order.id, 'dispute_id': dispute.id},
                )
        except Exception:
            pass

        return dispute


class DisputeResolveSerializer(serializers.Serializer):
    resolution = serializers.ChoiceField(choices=Dispute.Resolution.choices)
    note = serializers.CharField(required=False, allow_blank=True)
    refund_amount = serializers.IntegerField(required=False, min_value=0)

    def validate(self, data):
        dispute = self.context['dispute']
        resolution = data.get('resolution')
        refund_amount = data.get('refund_amount')

        if resolution == Dispute.Resolution.COMPROMISE and not refund_amount:
            raise serializers.ValidationError(
                "refund_amount is required for compromise resolution."
            )
        if refund_amount and refund_amount > int(dispute.order.agreed_price):
            raise serializers.ValidationError(
                "Refund amount cannot exceed order price."
            )
        return data

    def save(self):
        dispute = self.context['dispute']
        request = self.context['request']

        dispute.resolve(
            resolution=self.validated_data['resolution'],
            resolved_by=request.user,
            note=self.validated_data.get('note', ''),
            refund_amount=self.validated_data.get('refund_amount'),
        )

        # Notify both parties
        for user in [dispute.order.client, dispute.order.editor]:
            if not user:
                continue
            try:
                create_notification(
                    recipient=user,
                    notification_type=Notification.Type.ORDER,
                    title="Dispute resolved",
                    message=f"Dispute for order #{dispute.order_id} has been resolved: {dispute.resolution}.",
                    data={'order_id': dispute.order_id, 'dispute_id': dispute.id},
                )
            except Exception:
                pass

        return dispute


class DisputeMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1)
    is_admin_note = serializers.BooleanField(default=False, required=False)

    def validate_is_admin_note(self, value):
        request = self.context['request']
        if value and not request.user.is_staff:
            raise serializers.ValidationError("Only admin can create admin notes.")
        return value

    def save(self):
        dispute = self.context['dispute']
        request = self.context['request']

        msg = DisputeMessage.objects.create(
            dispute=dispute,
            sender=request.user,
            message=self.validated_data['message'],
            is_admin_note=self.validated_data.get('is_admin_note', False),
        )

        # Notify the other party (not the sender)
        order = dispute.order
        if request.user == order.client:
            notify_user = order.editor
        elif request.user == order.editor:
            notify_user = order.client
        else:
            notify_user = None

        if notify_user and not self.validated_data.get('is_admin_note'):
            try:
                create_notification(
                    recipient=notify_user,
                    notification_type=Notification.Type.ORDER,
                    title="New message in dispute",
                    message=f"New message in dispute for order #{order.id}.",
                    data={'order_id': order.id, 'dispute_id': dispute.id},
                )
            except Exception:
                pass

        return msg