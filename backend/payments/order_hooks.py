"""
payments/order_hooks.py
اتصال سیستم پرداخت به چرخه سفارش‌ها
این توابع از orders/views.py فراخوانی می‌شوند
"""
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone

from . import services as payment_services
from .models import Transaction


def on_order_submitted(order, actor):
    """
    هنگام ثبت سفارش توسط مشتری:
    اگر agreed_price > 0 باشد → مبلغ از کیف‌پول بلوکه می‌شود
    """
    if order.agreed_price and order.agreed_price > 0 and not order.escrow_held:
        with db_transaction.atomic():
            payment_services.hold_for_order(order, created_by=actor)
            order.escrow_held = True
            order.save(update_fields=["escrow_held", "updated_at"])


def on_order_cancelled(order, actor):
    """
    لغو سفارش → آزاد کردن escrow
    """
    if order.escrow_held and not order.payment_settled:
        with db_transaction.atomic():
            payment_services.release_escrow(order, created_by=actor)
            order.escrow_held = False
            order.save(update_fields=["escrow_held", "updated_at"])


def on_order_settlement(order, admin_user):
    """
    تسویه نهایی:
    - از کیف‌پول مشتری کسر می‌شود
    - کمیسیون محاسبه
    - به ادیتور واریز می‌شود
    - فیلدهای order آپدیت می‌شوند
    """
    if order.payment_settled:
        raise ValueError("این سفارش قبلاً تسویه شده است.")
    if not order.editor:
        raise ValueError("سفارش ادیتور ندارد — تسویه ممکن نیست.")
    if not order.agreed_price or order.agreed_price <= 0:
        raise ValueError("مبلغ سفارش (agreed_price) تنظیم نشده.")

    with db_transaction.atomic():
        result = payment_services.settle_order(order, admin_user=admin_user)

        order.payment_settled = True
        order.commission_amount = result["commission"]
        order.editor_earning = result["editor_earning"]
        order.paid_at = timezone.now()
        order.save(update_fields=[
            "payment_settled", "commission_amount",
            "editor_earning", "paid_at", "updated_at",
        ])

    return result
