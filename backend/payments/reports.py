"""
payments/reports.py
منطق گزارش‌گیری و صورت‌حساب
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Transaction, PaymentRequest, Wallet, WithdrawRequest

User = get_user_model()


def get_admin_summary(date_from=None, date_to=None) -> dict:
    """
    داشبورد مالی ادمین — خلاصه همه تراکنش‌ها
    """
    tx_qs = Transaction.objects.filter(status=Transaction.Status.SUCCESS)
    pr_qs = PaymentRequest.objects.all()
    wr_qs = WithdrawRequest.objects.all()

    if date_from:
        tx_qs = tx_qs.filter(created_at__gte=date_from)
        pr_qs = pr_qs.filter(created_at__gte=date_from)
        wr_qs = wr_qs.filter(created_at__gte=date_from)
    if date_to:
        tx_qs = tx_qs.filter(created_at__lte=date_to)
        pr_qs = pr_qs.filter(created_at__lte=date_to)
        wr_qs = wr_qs.filter(created_at__lte=date_to)

    def agg(qs, tx_type):
        r = qs.filter(tx_type=tx_type).aggregate(s=Sum("amount"))
        return r["s"] or Decimal("0")

    wallet_agg = Wallet.objects.aggregate(
        total_frozen=Sum("frozen_balance"),
        total_wallets=Count("id"),
    )

    pending_wr = WithdrawRequest.objects.filter(status=WithdrawRequest.Status.PENDING).aggregate(
        count=Count("id"),
        amount=Sum("amount"),
    )

    failed_payments = pr_qs.filter(status=PaymentRequest.Status.FAILED).count()

    if date_from and date_to:
        period_label = f"{date_from.date()} تا {date_to.date()}"
    elif date_from:
        period_label = f"از {date_from.date()}"
    elif date_to:
        period_label = f"تا {date_to.date()}"
    else:
        period_label = "کل دوره"

    return {
        "total_deposits": agg(tx_qs, Transaction.TxType.DEPOSIT),
        "total_payments": agg(tx_qs, Transaction.TxType.PAYMENT),
        "total_commissions": agg(tx_qs, Transaction.TxType.COMMISSION),
        "total_editor_earnings": agg(tx_qs, Transaction.TxType.EDITOR_EARNING),
        "total_withdrawals": agg(tx_qs, Transaction.TxType.WITHDRAWAL),
        "pending_withdrawals_count": pending_wr["count"] or 0,
        "pending_withdrawals_amount": pending_wr["amount"] or Decimal("0"),
        "total_wallets": wallet_agg["total_wallets"] or 0,
        "total_frozen": wallet_agg["total_frozen"] or Decimal("0"),
        "failed_payments_count": failed_payments,
        "period_label": period_label,
    }


def get_user_invoice(user, date_from=None, date_to=None) -> dict:
    """
    صورت‌حساب کاربر — تاریخچه کامل مالی
    """
    wallet = Wallet.objects.filter(user=user).first()

    tx_qs = Transaction.objects.filter(
        wallet__user=user,
        status=Transaction.Status.SUCCESS,
    ).select_related("order").order_by("-created_at")

    pr_qs = PaymentRequest.objects.filter(user=user).order_by("-created_at")

    if date_from:
        tx_qs = tx_qs.filter(created_at__gte=date_from)
        pr_qs = pr_qs.filter(created_at__gte=date_from)
    if date_to:
        tx_qs = tx_qs.filter(created_at__lte=date_to)
        pr_qs = pr_qs.filter(created_at__lte=date_to)

    def agg(tx_type):
        r = tx_qs.filter(tx_type=tx_type).aggregate(s=Sum("amount"))
        return r["s"] or Decimal("0")

    import uuid
    invoice_number = f"INV-{user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

    return {
        "invoice_number": invoice_number,
        "user_username": user.username,
        "user_email": user.email,
        "user_full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "generated_at": timezone.now(),
        "period_from": date_from,
        "period_to": date_to,
        "transactions": list(tx_qs),
        "payment_requests": list(pr_qs),
        "total_deposited": agg(Transaction.TxType.DEPOSIT),
        "total_spent": agg(Transaction.TxType.PAYMENT),
        "total_earned": agg(Transaction.TxType.EDITOR_EARNING),
        "total_withdrawn": agg(Transaction.TxType.WITHDRAWAL),
        "current_balance": wallet.balance if wallet else Decimal("0"),
        "withdrawable_balance": wallet.withdrawable_balance if wallet else Decimal("0"),
    }


def get_pending_payments():
    """پرداخت‌های در انتظار — برای پیگیری مجدد"""
    return PaymentRequest.objects.filter(
        status=PaymentRequest.Status.REDIRECTED,
    ).select_related("user", "order").order_by("-created_at")


def get_payment_status_breakdown(date_from=None, date_to=None) -> list:
    """تفکیک وضعیت پرداخت‌ها"""
    qs = PaymentRequest.objects.all()
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)

    result = qs.values("status", "gateway").annotate(
        count=Count("id"),
        total=Sum("amount"),
    ).order_by("gateway", "status")

    return list(result)
