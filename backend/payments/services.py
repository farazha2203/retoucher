"""
payments/services.py
لایه سرویس — همه منطق مالی اینجاست، نه در views
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    PaymentRequest,
    SiteCommissionSetting,
    Transaction,
    Wallet,
    WithdrawRequest,
)

User = get_user_model()


# ─── Wallet ──────────────────────────────────────────────────────────────────


def get_or_create_wallet(user) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def deduct_editor_penalty(
    *,
    editor,
    amount: Decimal,
    order=None,
    created_by=None,
    description: str = "",
    meta: dict | None = None,
) -> Transaction:
    """Deduct a confirmed penalty from an editor's earned, withdrawable funds.

    The wallet row is locked so two concurrent penalty/withdrawal requests cannot
    spend the same balance. Penalties never drive wallet balances below zero.
    """
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValidationError("مبلغ جریمه باید بیشتر از صفر باشد.")

    wallet, _ = Wallet.objects.get_or_create(user=editor)
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    if wallet.balance < amount or wallet.withdrawable_balance < amount:
        raise ValidationError(
            "موجودی قابل برداشت ادیتور برای اعمال این جریمه کافی نیست."
        )

    balance_before = wallet.balance
    withdrawable_before = wallet.withdrawable_balance

    wallet.balance -= amount
    wallet.withdrawable_balance -= amount
    wallet.save(
        update_fields=["balance", "withdrawable_balance", "updated_at"]
    )

    transaction_meta = {
        "withdrawable_balance_before": str(withdrawable_before),
        "withdrawable_balance_after": str(wallet.withdrawable_balance),
    }
    transaction_meta.update(meta or {})

    return _record_transaction(
        wallet=wallet,
        tx_type=Transaction.TxType.PENALTY,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        order=order,
        description=description,
        created_by=created_by,
        meta=transaction_meta,
    )

def get_order_amount(order) -> Decimal:
    """
    مبلغ مالی سفارش را برمی‌گرداند.
    فعلاً از agreed_price اگر وجود داشته باشد استفاده می‌کند،
    در غیر این صورت از price.
    اگر هیچ‌کدام وجود نداشت، خطای واضح می‌دهد.
    """
    amount = getattr(order, "agreed_price", None)

    if amount is None:
        amount = getattr(order, "price", None)

    if amount is None:
        raise ValidationError("مبلغ سفارش برای عملیات مالی تنظیم نشده است.")

    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValidationError("مبلغ سفارش باید بیشتر از صفر باشد.")

    return amount


def _record_transaction(
    wallet: Wallet,
    tx_type: str,
    amount: Decimal,
    balance_after: Decimal,
    order=None,
    payment_request=None,
    description: str = "",
    created_by=None,
    meta: dict = None,
    status: str = Transaction.Status.SUCCESS,
    balance_before: Decimal | None = None,
) -> Transaction:
    if balance_before is None:
        if tx_type in [
            Transaction.TxType.PAYMENT,
            Transaction.TxType.WITHDRAWAL,
            Transaction.TxType.PENALTY,
        ]:
            balance_before = balance_after + amount
        elif tx_type in [
            Transaction.TxType.DEPOSIT,
            Transaction.TxType.EDITOR_EARNING,
            Transaction.TxType.REFUND,
            Transaction.TxType.ADMIN_ADJUSTMENT,
        ]:
            balance_before = balance_after - amount
        else:
            balance_before = balance_after

    return Transaction.objects.create(
        wallet=wallet,
        tx_type=tx_type,
        status=status,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        order=order,
        payment_request=payment_request,
        description=description,
        created_by=created_by,
        meta=meta or {},
    )


# ─── شارژ کیف‌پول (دستی توسط ادمین) ─────────────────────────────────────────


@transaction.atomic
def admin_deposit(user, amount: Decimal, admin_user, description: str = "") -> Transaction:
    """ادمین مستقیم کیف‌پول کاربر را شارژ می‌کند"""
    if amount <= 0:
        raise ValidationError("مبلغ باید مثبت باشد.")
    wallet = get_or_create_wallet(user)
    wallet.credit(amount)
    wallet.refresh_from_db()
    return _record_transaction(
        wallet=wallet,
        tx_type=Transaction.TxType.DEPOSIT,
        amount=amount,
        balance_after=wallet.balance,
        description=description or f"شارژ دستی توسط {admin_user.username}",
        created_by=admin_user,
    )


# ─── Escrow (بلوکه کردن برای سفارش) ─────────────────────────────────────────


@transaction.atomic
def hold_for_order(order, created_by=None) -> Transaction:
    """
    هنگام ثبت سفارش، مبلغ را از موجودی مشتری بلوکه کن.
    order باید فیلد price داشته باشد.
    """
    amount = get_order_amount(order)
    wallet = get_or_create_wallet(order.client)
    if not wallet.can_afford(amount):
        raise ValidationError("موجودی کیف‌پول کافی نیست.")
    wallet.freeze(amount)
    wallet.refresh_from_db()
    return _record_transaction(
        wallet=wallet,
        tx_type=Transaction.TxType.ESCROW_HOLD,
        amount=amount,
        balance_after=wallet.balance,
        order=order,
        description=f"بلوکه برای سفارش #{order.id}",
        created_by=created_by,
    )


@transaction.atomic
def release_escrow(order, created_by=None) -> Transaction:
    """لغو سفارش → آزاد کردن مبلغ بلوکه‌شده"""
    amount = get_order_amount(order)
    wallet = get_or_create_wallet(order.client)
    wallet.unfreeze(amount)
    wallet.refresh_from_db()
    return _record_transaction(
        wallet=wallet,
        tx_type=Transaction.TxType.ESCROW_RELEASE,
        amount=amount,
        balance_after=wallet.balance,
        order=order,
        description=f"آزاد از escrow (لغو سفارش #{order.id})",
        created_by=created_by,
    )


# ─── تسویه سفارش (Settlement) ────────────────────────────────────────────────


@transaction.atomic
def settle_order(order, admin_user) -> dict:
    """
    تسویه نهایی سفارش تکمیل‌شده:
    1. کسر از موجودی مشتری (deduct frozen)
    2. کمیسیون سایت محاسبه می‌شود
    3. مانده به کیف‌پول ادیتور واریز می‌شود
    Returns: {commission, editor_earning, client_tx, commission_tx, editor_tx}
    """
    amount = get_order_amount(order)

    if getattr(order, "payment_settled", False):
        raise ValidationError("این سفارش قبلاً تسویه شده است.")

    if order.editor_id is None:
        raise ValidationError("برای تسویه، سفارش باید ادیتور داشته باشد.")

    allowed_statuses = {
        order.Status.COMPLETED,
        order.Status.SETTLEMENT_PENDING,
    }
    if order.status not in allowed_statuses:
        raise ValidationError(
            "فقط سفارش تکمیل‌شده یا در انتظار تسویه قابل پرداخت است."
        )
    
    commission_setting = SiteCommissionSetting.get_active()
    if not commission_setting:
        raise ValidationError("تنظیمات کمیسیون فعالی وجود ندارد.")

    commission_amount, editor_earning = commission_setting.calculate(amount)

    # 1. کسر از کیف‌پول مشتری
    client_wallet = get_or_create_wallet(order.client)
    client_wallet.deduct_frozen(amount)
    client_wallet.refresh_from_db()
    client_tx = _record_transaction(
        wallet=client_wallet,
        tx_type=Transaction.TxType.PAYMENT,
        amount=amount,
        balance_after=client_wallet.balance,
        order=order,
        description=f"پرداخت سفارش #{order.id}",
        created_by=admin_user,
        meta={"commission": str(commission_amount), "editor_earning": str(editor_earning)},
    )

    # 2. کمیسیون سایت (فقط log — به wallet سایت نمی‌رود، به عنوان audit)
    commission_tx = Transaction.objects.create(
        wallet=client_wallet,
        tx_type=Transaction.TxType.COMMISSION,
        status=Transaction.Status.SUCCESS,
        amount=commission_amount,
        balance_before=client_wallet.balance,
        balance_after=client_wallet.balance,
        order=order,
        description=f"کمیسیون {commission_setting.commission_percent}٪ سفارش #{order.id}",
        created_by=admin_user,
        meta={"commission_percent": str(commission_setting.commission_percent)},
    )

    # 3. واریز به کیف‌پول ادیتور
    editor_wallet = get_or_create_wallet(order.editor)
    editor_wallet.credit_withdrawable(editor_earning)
    editor_wallet.refresh_from_db()
    editor_tx = _record_transaction(
        wallet=editor_wallet,
        tx_type=Transaction.TxType.EDITOR_EARNING,
        amount=editor_earning,
        balance_after=editor_wallet.balance,
        order=order,
        description=f"درآمد سفارش #{order.id} (پس از {commission_setting.commission_percent}٪ کمیسیون)",
        created_by=admin_user,
        meta={"original_amount": str(amount), "commission": str(commission_amount)},
    )

    # Workflow is the single source of truth for order state changes.
    # Import locally to keep the payments module decoupled during app loading.
    from orders.workflow import transition_order

    now = timezone.now()

    if order.status == order.Status.COMPLETED:
        order = transition_order(
            order=order,
            to_status=order.Status.SETTLEMENT_PENDING,
            actor=admin_user,
            note="Settlement started.",
            extra_updates={
                "settlement_started_at": order.settlement_started_at or now,
            },
        )

    order = transition_order(
        order=order,
        to_status=order.Status.PAID,
        actor=admin_user,
        note="Financial settlement completed.",
        extra_updates={
            "commission_amount": commission_amount,
            "editor_earning": editor_earning,
            "escrow_held": False,
            "payment_settled": True,
            "paid_at": now,
        },
    )

    return {
        "commission": commission_amount,
        "editor_earning": editor_earning,
        "client_tx": client_tx,
        "commission_tx": commission_tx,
        "editor_tx": editor_tx,
    }


# ─── برداشت ادیتور ──────────────────────────────────────────────────────────


@transaction.atomic
def request_withdrawal(editor, amount: Decimal, bank_info: dict) -> WithdrawRequest:
    """ادیتور درخواست برداشت ثبت می‌کند"""
    wallet = get_or_create_wallet(editor)
    if wallet.withdrawable_balance < amount:
        raise ValidationError(
            f"موجودی قابل برداشت ({wallet.withdrawable_balance} تومان) کافی نیست."
        )
    if amount <= 0:
        raise ValidationError("مبلغ برداشت باید مثبت باشد.")

    # موجودی رو pending نگه می‌داریم تا تأیید ادمین
    return WithdrawRequest.objects.create(
        editor=editor,
        amount=amount,
        **bank_info,
    )


@transaction.atomic
def approve_withdrawal(withdraw_request: WithdrawRequest, admin_user) -> Transaction:
    """ادمین درخواست برداشت را تأیید می‌کند"""
    if withdraw_request.status != WithdrawRequest.Status.PENDING:
        raise ValidationError("فقط درخواست‌های در انتظار قابل تأیید هستند.")

    wallet = get_or_create_wallet(withdraw_request.editor)
    wallet.deduct_withdrawable(withdraw_request.amount)
    wallet.refresh_from_db()

    withdraw_request.status = WithdrawRequest.Status.APPROVED
    withdraw_request.reviewed_by = admin_user
    withdraw_request.reviewed_at = timezone.now()
    withdraw_request.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

    return _record_transaction(
        wallet=wallet,
        tx_type=Transaction.TxType.WITHDRAWAL,
        amount=withdraw_request.amount,
        balance_after=wallet.balance,
        description=f"برداشت تأیید شده #{withdraw_request.id}",
        created_by=admin_user,
    )


@transaction.atomic
def mark_withdrawal_paid(withdraw_request: WithdrawRequest, admin_user):
    """ادمین تأیید می‌کند که پول واریز شد"""
    if withdraw_request.status != WithdrawRequest.Status.APPROVED:
        raise ValidationError("فقط درخواست‌های تأیید‌شده قابل پرداخت هستند.")
    withdraw_request.status = WithdrawRequest.Status.PAID
    withdraw_request.paid_at = timezone.now()
    withdraw_request.admin_note = (withdraw_request.admin_note or "") + f"\nپرداخت توسط {admin_user.username}"
    withdraw_request.save(update_fields=["status", "paid_at", "admin_note", "updated_at"])


@transaction.atomic
def reject_withdrawal(withdraw_request: WithdrawRequest, admin_user, note: str = "") -> None:
    """ادمین درخواست برداشت را رد می‌کند — موجودی برمی‌گردد"""
    if withdraw_request.status != WithdrawRequest.Status.PENDING:
        raise ValidationError("فقط درخواست‌های در انتظار قابل رد هستند.")

    withdraw_request.status = WithdrawRequest.Status.REJECTED
    withdraw_request.reviewed_by = admin_user
    withdraw_request.reviewed_at = timezone.now()
    withdraw_request.admin_note = note
    withdraw_request.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_note", "updated_at"])
