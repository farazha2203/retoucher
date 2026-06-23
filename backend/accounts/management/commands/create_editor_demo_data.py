from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import EditorPortfolioItem, EditorProfile
from catalog.models import EditStyle


class Command(BaseCommand):
    help = "Create demo editor profiles and skills"

    def handle(self, *args, **options):
        User = get_user_model()

        editors_data = [
            {
                "username": "editor01",
                "email": "editor01@example.com",
                "password": "EditorPass123!",
                "display_name": "Editor One",
                "bio": "Beauty and portrait retouch specialist.",
                "level": EditorProfile.EditorLevel.PRO,
                "base_price": 350000,
                "average_delivery_hours": 24,
                "rating_average": 4.80,
                "completed_orders_count": 42,
                "skills": ["natural-beauty", "high-end-beauty", "russian-portrait"],
            },
            {
                "username": "editor02",
                "email": "editor02@example.com",
                "password": "EditorPass123!",
                "display_name": "Editor Two",
                "bio": "Wedding and color correction editor.",
                "level": EditorProfile.EditorLevel.SENIOR,
                "base_price": 250000,
                "average_delivery_hours": 36,
                "rating_average": 4.60,
                "completed_orders_count": 28,
                "skills": ["color-correction", "cinematic-color-grade", "wedding-premium"],
            },
            {
                "username": "editor03",
                "email": "editor03@example.com",
                "password": "EditorPass123!",
                "display_name": "Editor Three",
                "bio": "Product photo and background cleanup specialist.",
                "level": EditorProfile.EditorLevel.MID,
                "base_price": 180000,
                "average_delivery_hours": 24,
                "rating_average": 4.30,
                "completed_orders_count": 16,
                "skills": ["background-cleanup", "commercial-product-retouch"],
            },
        ]

        created_profiles = 0
        created_portfolio_items = 0

        for editor_data in editors_data:
            skills = editor_data.pop("skills")
            password = editor_data.pop("password")

            user, user_created = User.objects.get_or_create(
                username=editor_data["username"],
                defaults={
                    "email": editor_data["email"],
                    "is_active": True,
                },
            )

            if user_created:
                user.set_password(password)
                user.save(update_fields=["password"])

            profile, profile_created = EditorProfile.objects.update_or_create(
                user=user,
                defaults={
                    "display_name": editor_data["display_name"],
                    "bio": editor_data["bio"],
                    "level": editor_data["level"],
                    "base_price": editor_data["base_price"],
                    "average_delivery_hours": editor_data["average_delivery_hours"],
                    "rating_average": editor_data["rating_average"],
                    "completed_orders_count": editor_data["completed_orders_count"],
                    "is_available": True,
                    "accepts_direct_requests": True,
                    "accepts_public_requests": True,
                    "accepts_sample_challenges": True,
                },
            )

            if profile_created:
                created_profiles += 1

            style_objects = EditStyle.objects.filter(slug__in=skills)
            profile.skills.set(style_objects)

            for style in style_objects[:2]:
                item, item_created = EditorPortfolioItem.objects.update_or_create(
                    editor=profile,
                    style=style,
                    title=f"{style.title} sample",
                    defaults={
                        "description": f"Demo portfolio item for {style.title}.",
                        "is_featured": True,
                        "is_active": True,
                    },
                )

                if item_created:
                    created_portfolio_items += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Editor demo data created successfully. "
                f"Profiles created: {created_profiles}, "
                f"Portfolio items created: {created_portfolio_items}"
            )
        )