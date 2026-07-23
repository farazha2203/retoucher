from django.db.models import Q
from django.utils import timezone

from .models import StudioProfile


def active_studio_ads():
    now = timezone.now()
    return (
        StudioProfile.objects.select_related(
            "customer",
            "customer__tier",
            "customer__user",
        )
        .filter(
            is_verified=True,
            advertising_enabled=True,
        )
        .filter(Q(featured_until__isnull=True) | Q(featured_until__gt=now))
    )
