"""Bridge existing Retoucher Django ModelAdmin classes into SmartBase Admin.

The original ModelAdmin registrations remain on django.contrib.admin.site, so
the legacy admin keeps all existing behaviour. SmartBase receives adapter
classes that inherit both SBAdmin and each original ModelAdmin class.
"""

from __future__ import annotations

from functools import lru_cache

from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from django_smartbase_admin.admin.admin_base import (
    SBAdmin,
    SBAdminStackedInline,
    SBAdminTableInline,
)
from django_smartbase_admin.admin.site import sb_admin_site


@lru_cache(maxsize=None)
def _adapt_inline(inline_class):
    """Convert a standard Django inline class to its SmartBase counterpart."""
    if issubclass(inline_class, SBAdminTableInline) or issubclass(
        inline_class, SBAdminStackedInline
    ):
        return inline_class

    if issubclass(inline_class, admin.StackedInline):
        smartbase_base = SBAdminStackedInline
    else:
        # TabularInline is the default and also covers most project inlines.
        smartbase_base = SBAdminTableInline

    return type(
        f"SmartBase{inline_class.__name__}",
        (smartbase_base, inline_class),
        {
            "__module__": inline_class.__module__,
            "__doc__": inline_class.__doc__,
        },
    )


@lru_cache(maxsize=None)
def _adapt_model_admin(original_admin_class):
    """Create a SmartBase admin while retaining the original admin behaviour."""
    if issubclass(original_admin_class, SBAdmin):
        return original_admin_class

    original_inlines = getattr(original_admin_class, "inlines", ()) or ()
    adapted_inlines = tuple(_adapt_inline(inline) for inline in original_inlines)

    return type(
        f"SmartBase{original_admin_class.__name__}",
        (SBAdmin, original_admin_class),
        {
            "__module__": original_admin_class.__module__,
            "__doc__": original_admin_class.__doc__,
            "inlines": adapted_inlines,
        },
    )


def register_retoucher_admins() -> None:
    """Register every existing Retoucher ModelAdmin on SmartBase Admin.

    We intentionally use Django's existing registry as the single source of
    truth. Any current or future app admin registration is therefore mirrored
    automatically without maintaining another hard-coded model list.
    """
    for model, original_admin in list(admin.site._registry.items()):
        if model in sb_admin_site._registry:
            continue

        smartbase_admin_class = _adapt_model_admin(type(original_admin))

        try:
            sb_admin_site.register(model, smartbase_admin_class)
        except AlreadyRegistered:
            continue
