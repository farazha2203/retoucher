from decimal import Decimal

from django.db import transaction

from .models import OrderPricingSnapshot
from .pricing import calculate_order_pricing


@transaction.atomic
def lock_order_pricing(*, order, base_price, editor_profile=None):
    result = calculate_order_pricing(
        base_price=base_price,
        client=order.client,
        editor_profile=editor_profile,
    )

    snapshot, _ = OrderPricingSnapshot.objects.update_or_create(
        order=order,
        defaults={
            key: value
            for key, value in result.items()
            if key != "rule"
        }
        | {"rule": result.get("rule")},
    )

    order.agreed_price = snapshot.final_price
    order.commission_amount = (
        snapshot.site_commission_amount
        + snapshot.supervisor_amount
        + snapshot.expert_amount
    )
    order.editor_earning = snapshot.editor_earning
    order.save(
        update_fields=(
            "agreed_price",
            "commission_amount",
            "editor_earning",
            "updated_at",
        )
    )

    return snapshot
