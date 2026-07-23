from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from payments.models import Transaction, Wallet

from .models import (
    CustomerProfile,
    CustomerSubscription,
    CustomerTier,
)


class MembershipBillingError(Exception):
    pass


def get_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def get_customer_profile(user):
    default_tier = CustomerTier.objects.filter(
        code=CustomerTier.Code.NORMAL,
        is_active=True,
    ).first()

    profile, _ = CustomerProfile.objects.get_or_create(
        user=user,
        defaults={"tier": default_tier},
    )

    if profile.tier_id is None and default_tier is not None:
        profile.tier = default_tier
        profile.save(update_fields=("tier", "updated_at"))

    return profile


@transaction.atomic
def purchase_membership(*, user, tier: CustomerTier, period: str):
    if not tier.is_active or not tier.is_purchasable:
        raise MembershipBillingError("این پلن قابل خرید نیست.")

    if period not in {"monthly", "annual"}:
        raise MembershipBillingError("دوره اشتراک معتبر نیست.")

    amount = (
        Decimal(tier.monthly_price)
        if period == "monthly"
        else Decimal(tier.annual_price)
    )

    if amount <= 0:
        raise MembershipBillingError(
            "قیمت این پلن هنوز توسط مدیر تعیین نشده است."
        )

    wallet = get_wallet(user)

    if wallet.available_balance < amount:
        raise MembershipBillingError("موجودی کیف پول کافی نیست.")

    customer = get_customer_profile(user)

    starts_at = timezone.now()

    active = (
        CustomerSubscription.objects.filter(
            customer=customer,
            status=CustomerSubscription.Status.ACTIVE,
            ends_at__gt=starts_at,
        )
        .order_by("-ends_at")
        .first()
    )

    if active:
        starts_at = active.ends_at

    ends_at = (
        starts_at + timedelta(days=30)
        if period == "monthly"
        else starts_at + timedelta(days=365)
    )

    before = wallet.balance

    wallet.balance -= amount
    wallet.save(update_fields=("balance", "updated_at"))

    subscription = CustomerSubscription.objects.create(
        customer=customer,
        tier=tier,
        status=CustomerSubscription.Status.ACTIVE,
        starts_at=starts_at,
        ends_at=ends_at,
        purchased_amount=amount,
    )

    Transaction.objects.create(
        wallet=wallet,
        tx_type=Transaction.TxType.PAYMENT,
        status=Transaction.Status.SUCCESS,
        amount=amount,
        balance_before=before,
        balance_after=wallet.balance,
        description=f"خرید اشتراک {tier.title}",
        meta={
            "membership_id": subscription.pk,
            "period": period,
            "tier": tier.code,
        },
        created_by=user,
    )

    return subscription
