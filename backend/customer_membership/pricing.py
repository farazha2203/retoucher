from decimal import Decimal, ROUND_HALF_UP

from .models import CustomerProfile, PerformanceCommissionRule


def money(value):
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def resolve_customer_discount(user):
    profile = CustomerProfile.objects.filter(user=user).select_related("tier").first()
    return Decimal(profile.effective_discount_percent if profile else 0)


def resolve_commission_rule(editor_profile):
    if editor_profile is None:
        return None
    likes_count = getattr(editor_profile, "portfolio_likes_count", 0)
    return PerformanceCommissionRule.objects.filter(
        is_active=True,
        min_rating__lte=editor_profile.rating_average,
        min_likes__lte=likes_count,
    ).order_by("-min_rating", "-min_likes", "sort_order").first()


def calculate_order_pricing(*, base_price, client, editor_profile=None):
    base_price = money(base_price)
    discount_percent = resolve_customer_discount(client)
    discount_amount = money(base_price * discount_percent / Decimal("100"))
    final_price = max(Decimal("0"), base_price - discount_amount)
    rule = resolve_commission_rule(editor_profile)
    site_percent = Decimal(rule.site_commission_percent if rule else "10")
    supervisor_percent = Decimal(rule.supervisor_percent if rule else "0")
    expert_percent = Decimal(rule.expert_percent if rule else "0")
    site_amount = money(final_price * site_percent / Decimal("100"))
    supervisor_amount = money(final_price * supervisor_percent / Decimal("100"))
    expert_amount = money(final_price * expert_percent / Decimal("100"))
    editor_earning = max(Decimal("0"), final_price - site_amount - supervisor_amount - expert_amount)
    return {
        "base_price": base_price,
        "customer_discount_percent": discount_percent,
        "customer_discount_amount": discount_amount,
        "final_price": final_price,
        "site_commission_percent": site_percent,
        "site_commission_amount": site_amount,
        "supervisor_percent": supervisor_percent,
        "supervisor_amount": supervisor_amount,
        "expert_percent": expert_percent,
        "expert_amount": expert_amount,
        "editor_earning": money(editor_earning),
        "rule": rule,
    }
