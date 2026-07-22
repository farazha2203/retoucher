from collections import defaultdict

from django_smartbase_admin.admin.site import sb_admin_site
from django_smartbase_admin.engine.configuration import (
    SBAdminConfigurationBase,
    SBAdminRoleConfiguration,
)
from django_smartbase_admin.engine.menu_item import SBAdminMenuItem
from django_smartbase_admin.views.dashboard_view import SBAdminDashboardView

from config.sbadmin_registry import register_retoucher_admins


# Mirror all existing Retoucher ModelAdmin registrations before SmartBase
# creates its view map.
register_retoucher_admins()


APP_LABELS_FA = {
    "accounts": "کاربران و ادیتورها",
    "orders": "سفارش‌ها و گردش کار",
    "projects": "درخواست‌ها و پیشنهادها",
    "catalog": "کاتالوگ خدمات",
    "payments": "پرداخت‌ها و امور مالی",
    "notifications": "اعلان‌ها",
    "auth": "کاربران و دسترسی‌ها",
    "filer": "مدیریت فایل‌ها",
    "easy_thumbnails": "تصاویر بندانگشتی",
    "sb_admin_audit": "گزارش تغییرات",
}

APP_ICONS = {
    "accounts": "User-business",
    "orders": "Shopping-bag",
    "projects": "Box",
    "catalog": "Application-menu",
    "payments": "Bank-card",
    "notifications": "Attention",
    "auth": "Lock",
    "filer": "Picture-one",
    "easy_thumbnails": "Picture-one",
    "sb_admin_audit": "Table-report",
}

PREFERRED_ORDER = [
    "accounts",
    "orders",
    "projects",
    "catalog",
    "payments",
    "notifications",
    "auth",
    "filer",
    "easy_thumbnails",
    "sb_admin_audit",
]


def _registered_model_menu():
    grouped = defaultdict(list)

    for model in sb_admin_site._registry:
        opts = model._meta
        grouped[opts.app_label].append(
            SBAdminMenuItem(
                label=str(opts.verbose_name_plural),
                view_id=f"{opts.app_label}_{opts.model_name}",
            )
        )

    order_map = {name: index for index, name in enumerate(PREFERRED_ORDER)}
    menu_items = [
        SBAdminMenuItem(
            label="داشبورد مدیریت",
            icon="All-application",
            view_id="dashboard",
        )
    ]

    for app_label, children in sorted(
        grouped.items(),
        key=lambda item: (
            order_map.get(item[0], 999),
            APP_LABELS_FA.get(item[0], item[0]),
        ),
    ):
        children.sort(key=lambda item: str(item.label))

        menu_items.append(
            SBAdminMenuItem(
                label=APP_LABELS_FA.get(
                    app_label,
                    app_label.replace("_", " ").title(),
                ),
                icon=APP_ICONS.get(app_label, "Application"),
                sub_items=children,
            )
        )

    return menu_items


class RetoucherRoleConfiguration(SBAdminRoleConfiguration):
    """Use normal Django permissions and show every registered model to superusers."""

    pass


class SBAdminConfiguration(SBAdminConfigurationBase):
    def get_configuration_for_roles(self, user_roles):
        return RetoucherRoleConfiguration(
            default_view=SBAdminMenuItem(view_id="dashboard"),
            menu_items=_registered_model_menu(),
            registered_views=[
                SBAdminDashboardView(
                    widgets=[],
                    title="داشبورد مدیریت ریتاچر",
                )
            ],
        )
