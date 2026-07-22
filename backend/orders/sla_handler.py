"""
SLA enforcement and penalty calculation.
"""
from decimal import Decimal
from django.utils import timezone
from .models import Order, OrderDelivery
from .sla_models import DeliveryPenalty, SLAConfig
from notifications.models import Notification
from notifications.services import create_notification


class SLAHandler:
    """Handle SLA checks and penalty creation."""

    @staticmethod
    def calculate_penalty(order, delivered_at=None):
        """
        Calculate penalty for a late order.

        Returns:
            dict: {
                'is_late': bool,
                'days_late': int,
                'penalty_amount': Decimal,
                'penalty_percent': Decimal,
            }
        """
        if not order.deadline:
            return {'is_late': False, 'days_late': 0, 'penalty_amount': Decimal('0'), 'penalty_percent': Decimal('0')}

        config = SLAConfig.get_active()
        reference_time = delivered_at or timezone.now()

        # Check grace period
        grace_deadline = order.deadline + __import__('datetime').timedelta(hours=config.grace_period_hours)

        if reference_time <= grace_deadline:
            return {'is_late': False, 'days_late': 0, 'penalty_amount': Decimal('0'), 'penalty_percent': Decimal('0')}

        # Calculate days late (after grace period)
        seconds_late = (reference_time - order.deadline).total_seconds()
        days_late = max(1, int(seconds_late / 86400))

        # Calculate penalty
        penalty_percent = min(
            config.penalty_percent_per_day * days_late,
            config.max_penalty_percent,
        )

        penalty_amount = (order.agreed_price * penalty_percent / 100).quantize(Decimal('1'))

        return {
            'is_late': True,
            'days_late': days_late,
            'penalty_amount': penalty_amount,
            'penalty_percent': penalty_percent,
        }

    @staticmethod
    def check_order_and_create_penalty(order):
        """
        Check if order is late and create penalty if needed.
        Called when order is delivered or by periodic task.

        Returns:
            DeliveryPenalty or None
        """
        if not order.deadline:
            return None

        # Already has penalty
        if order.penalties.filter(
            penalty_type=DeliveryPenalty.PenaltyType.LATE_DELIVERY
        ).exists():
            return None

        # Get delivery time
        latest_delivery = order.deliveries.order_by('-uploaded_at').first()
        delivered_at = latest_delivery.uploaded_at if latest_delivery else None

        result = SLAHandler.calculate_penalty(order, delivered_at)

        if not result['is_late']:
            return None

        # Create penalty
        penalty = DeliveryPenalty.objects.create(
            order=order,
            editor=order.editor,
            penalty_type=DeliveryPenalty.PenaltyType.LATE_DELIVERY,
            order_amount=order.agreed_price,
            penalty_amount=result['penalty_amount'],
            penalty_percent=result['penalty_percent'],
            deadline=order.deadline,
            delivered_at=delivered_at,
            days_late=result['days_late'],
            reason=f"Order delivered {result['days_late']} day(s) late.",
        )

        # Notify editor
        try:
            create_notification(
                recipient=order.editor,
                notification_type=Notification.Type.ORDER,
                title="Late delivery penalty",
                message=f"A penalty of {int(result['penalty_amount'])} tomans has been applied for late delivery on order #{order.id}.",
                priority=Notification.Priority.HIGH,
                data={
                    'order_id': order.id,
                    'penalty_id': penalty.id,
                    'penalty_amount': int(result['penalty_amount']),
                    'days_late': result['days_late'],
                },
            )
        except Exception as e:
            print(f"Error creating SLA notification: {e}")

        # Notify admin
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                create_notification(
                    recipient=admin,
                    notification_type=Notification.Type.ORDER,
                    title="Late delivery penalty created",
                    message=f"Penalty created for order #{order.id} - {int(result['penalty_amount'])} tomans.",
                    data={
                        'order_id': order.id,
                        'penalty_id': penalty.id,
                    },
                )
        except Exception as e:
            print(f"Error creating admin SLA notification: {e}")

        return penalty

    @staticmethod
    def check_all_late_orders():
        """
        Check all in-progress orders for SLA violations.
        Called by celery beat task.
        """
        from datetime import timedelta

        now = timezone.now()
        late_count = 0

        # Find overdue orders (past deadline, not yet delivered)
        overdue_orders = Order.objects.filter(
            deadline__lt=now,
            status__in=[
                Order.Status.IN_PROGRESS,
                Order.Status.ASSIGNED,
                Order.Status.REVISION_REQUIRED,
            ],
            editor__isnull=False,
        ).exclude(
            penalties__penalty_type=DeliveryPenalty.PenaltyType.LATE_DELIVERY
        )

        for order in overdue_orders:
            penalty = SLAHandler.check_order_and_create_penalty(order)
            if penalty:
                late_count += 1

        return late_count