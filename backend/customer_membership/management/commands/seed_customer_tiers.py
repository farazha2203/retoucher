from django.core.management.base import BaseCommand
from customer_membership.models import CustomerTier


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        rows = [
            dict(code="normal", title="مشتری عادی", discount_percent=0, priority_level=0, badge_title="مشتری", badge_color="#A8A3B3", is_purchasable=False, sort_order=10),
            dict(code="studio", title="آتلیه‌دار", description="۱۰٪ تخفیف و اولویت پردازش", discount_percent=10, priority_level=10, badge_title="Studio Partner", badge_color="#85BFA7", logo_enabled=True, sort_order=20),
            dict(code="studio_vip", title="آتلیه‌دار VIP", description="تخفیف بیشتر، تبلیغات و بالاترین اولویت", discount_percent=15, priority_level=20, badge_title="VIP Studio", badge_color="#C49BE8", advertising_enabled=True, logo_enabled=True, featured_listing_enabled=True, sort_order=30),
        ]
        for row in rows:
            CustomerTier.objects.update_or_create(code=row["code"], defaults=row)
            self.stdout.write(self.style.SUCCESS(f"OK {row['code']}"))
