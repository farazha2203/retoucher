"""
payments/gateway_zarinpal.py
ادغام با API زرین‌پال (v4)
"""

import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

from .models import PaymentRequest, Transaction, Wallet
from . import services as payment_services

logger = logging.getLogger(__name__)

ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_STARTPAY_URL = "https://www.zarinpal.com/pg/StartPay/{authority}"

# برای تست از sandbox استفاده کن
ZARINPAL_SANDBOX_REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_SANDBOX_VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_SANDBOX_STARTPAY_URL = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"


def _get_merchant_id() -> str:
    merchant_id = getattr(settings, "ZARINPAL_MERCHANT_ID", "")
    if not merchant_id:
        raise ValueError("ZARINPAL_MERCHANT_ID در settings تعریف نشده.")
    return merchant_id


def _is_sandbox() -> bool:
    return getattr(settings, "ZARINPAL_SANDBOX", True)


def _request_url():
    return ZARINPAL_SANDBOX_REQUEST_URL if _is_sandbox() else ZARINPAL_REQUEST_URL


def _verify_url():
    return ZARINPAL_SANDBOX_VERIFY_URL if _is_sandbox() else ZARINPAL_VERIFY_URL


def _startpay_url(authority: str) -> str:
    base = ZARINPAL_SANDBOX_STARTPAY_URL if _is_sandbox() else ZARINPAL_STARTPAY_URL
    return base.format(authority=authority)


def create_payment(
    user,
    amount: Decimal,
    callback_url: str,
    description: str = "شارژ کیف‌پول ریتاچر",
    order=None,
) -> dict:
    """
    یک PaymentRequest می‌سازد و Authority از زرین‌پال می‌گیرد.
    Returns: {"payment_request": pr, "payment_url": url} یا raise می‌کند
    """
    # مبلغ باید به ریال باشد — تومان × 10
    amount_rial = int(amount) * 10

    pr = PaymentRequest.objects.create(
        user=user,
        gateway=PaymentRequest.Gateway.ZARINPAL,
        amount=amount,
        description=description,
        callback_url=callback_url,
        order=order,
    )

    payload = {
        "merchant_id": _get_merchant_id(),
        "amount": amount_rial,
        "description": description,
        "callback_url": callback_url,
        "metadata": {
            "payment_request_id": pr.id,
            "user_id": user.id,
        },
    }

    try:
        resp = requests.post(_request_url(), json=payload, timeout=15)
        data = resp.json()
    except Exception as exc:
        logger.error("Zarinpal request error: %s", exc)
        pr.status = PaymentRequest.Status.FAILED
        pr.gateway_response = {"error": str(exc)}
        pr.save(update_fields=["status", "gateway_response"])
        raise ValueError(f"خطا در اتصال به زرین‌پال: {exc}")

    pr.gateway_response = data
    code = data.get("data", {}).get("code")

    if code == 100:
        authority = data["data"]["authority"]
        pr.authority = authority
        pr.status = PaymentRequest.Status.REDIRECTED
        pr.save(update_fields=["authority", "status", "gateway_response"])
        return {
            "payment_request": pr,
            "payment_url": _startpay_url(authority),
        }
    else:
        pr.status = PaymentRequest.Status.FAILED
        pr.save(update_fields=["status", "gateway_response"])
        error_msg = data.get("errors", {}).get("message", "خطای ناشناخته زرین‌پال")
        raise ValueError(f"زرین‌پال خطا داد: {error_msg} (code={code})")


def verify_payment(authority: str, status_param: str) -> PaymentRequest:
    """
    callback زرین‌پال → تأیید پرداخت و شارژ کیف‌پول
    status_param: مقدار ?Status= در callback URL
    Returns: PaymentRequest آپدیت شده
    """
    try:
        pr = PaymentRequest.objects.select_for_update().get(authority=authority)
    except PaymentRequest.DoesNotExist:
        raise ValueError("PaymentRequest با این authority یافت نشد.")

    if pr.status == PaymentRequest.Status.SUCCESS:
        # از double-verification جلوگیری کن
        return pr

    if status_param != "OK":
        pr.status = PaymentRequest.Status.CANCELLED
        pr.save(update_fields=["status"])
        raise ValueError("پرداخت توسط کاربر لغو شد.")

    # تأیید از زرین‌پال
    amount_rial = int(pr.amount) * 10
    payload = {
        "merchant_id": _get_merchant_id(),
        "amount": amount_rial,
        "authority": authority,
    }

    try:
        resp = requests.post(_verify_url(), json=payload, timeout=15)
        data = resp.json()
    except Exception as exc:
        logger.error("Zarinpal verify error: %s", exc)
        raise ValueError(f"خطا در تأیید با زرین‌پال: {exc}")

    pr.gateway_response = {**pr.gateway_response, "verify": data}
    code = data.get("data", {}).get("code")

    if code in (100, 101):  # 101 = already verified
        ref_id = str(data["data"].get("ref_id", ""))
        pr.ref_id = ref_id
        pr.status = PaymentRequest.Status.SUCCESS
        pr.paid_at = timezone.now()
        pr.save(update_fields=["ref_id", "status", "paid_at", "gateway_response"])

        # شارژ کیف‌پول
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            wallet = payment_services.get_or_create_wallet(pr.user)
            wallet.credit(pr.amount)
            wallet.refresh_from_db()
            Transaction.objects.create(
                wallet=wallet,
                tx_type=Transaction.TxType.DEPOSIT,
                status=Transaction.Status.SUCCESS,
                amount=pr.amount,
                balance_before=wallet.balance - pr.amount,
                balance_after=wallet.balance,
                payment_request=pr,
                order=pr.order,
                description=f"شارژ از زرین‌پال (ref_id={ref_id})",
                meta={"authority": authority, "ref_id": ref_id},
            )
        return pr
    else:
        pr.status = PaymentRequest.Status.FAILED
        pr.save(update_fields=["status", "gateway_response"])
        error_msg = data.get("errors", {}).get("message", "تأیید ناموفق")
        raise ValueError(f"تأیید زرین‌پال ناموفق: {error_msg} (code={code})")
