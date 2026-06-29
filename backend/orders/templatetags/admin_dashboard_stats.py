from django import template
from django.contrib.auth import get_user_model

register = template.Library()


@register.simple_tag
def retoucher_admin_stats():
    stats = {
        "orders_count": 0,
        "public_pending_deliveries_count": 0,
        "payment_requests_count": 0,
        "pending_withdrawals_count": 0,
        "transactions_count": 0,
        "users_count": 0,
    }

    try:
        from orders.models import Order, OrderDelivery

        stats["orders_count"] = Order.objects.count()

        pending_status = getattr(
            OrderDelivery.PublicationStatus,
            "PENDING",
            "pending",
        )

        stats["public_pending_deliveries_count"] = OrderDelivery.objects.filter(
            publication_status=pending_status,
        ).count()
    except Exception:
        pass

    try:
        from payments.models import PaymentRequest, Transaction, WithdrawRequest

        stats["payment_requests_count"] = PaymentRequest.objects.count()
        stats["transactions_count"] = Transaction.objects.count()

        pending_withdraw_status = "pending"

        status_field = WithdrawRequest._meta.get_field("status")
        choices = dict(status_field.choices or [])

        if "pending" not in choices:
            for value in choices.keys():
                if str(value).lower() == "pending":
                    pending_withdraw_status = value
                    break

        stats["pending_withdrawals_count"] = WithdrawRequest.objects.filter(
            status=pending_withdraw_status,
        ).count()
    except Exception:
        pass

    try:
        User = get_user_model()
        stats["users_count"] = User.objects.count()
    except Exception:
        pass

    return stats
