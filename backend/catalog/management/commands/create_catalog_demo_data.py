from django.core.management.base import BaseCommand

from catalog.models import EditCategory, EditPackage, EditStyle


class Command(BaseCommand):
    help = "Create demo edit catalog data"

    def handle(self, *args, **options):
        catalog_data = [
            {
                "title": "Beauty Retouch",
                "slug": "beauty-retouch",
                "description": "Skin cleanup, face retouching, beauty and portrait enhancement.",
                "sort_order": 1,
                "styles": [
                    {
                        "title": "Natural Beauty",
                        "slug": "natural-beauty",
                        "description": "Clean natural retouch with realistic skin texture.",
                        "min_price": 150000,
                        "max_price": 500000,
                        "suggested_price": 300000,
                        "estimated_delivery_hours": 24,
                    },
                    {
                        "title": "High-End Beauty",
                        "slug": "high-end-beauty",
                        "description": "Advanced beauty retouch for professional portraits and campaigns.",
                        "min_price": 500000,
                        "max_price": 1500000,
                        "suggested_price": 900000,
                        "estimated_delivery_hours": 48,
                    },
                ],
            },
            {
                "title": "Color and Light",
                "slug": "color-and-light",
                "description": "Color correction, exposure balancing, tone and mood editing.",
                "sort_order": 2,
                "styles": [
                    {
                        "title": "Color Correction",
                        "slug": "color-correction",
                        "description": "Fixing white balance, exposure, contrast and basic colors.",
                        "min_price": 80000,
                        "max_price": 250000,
                        "suggested_price": 150000,
                        "estimated_delivery_hours": 12,
                    },
                    {
                        "title": "Cinematic Color Grade",
                        "slug": "cinematic-color-grade",
                        "description": "Creative color grading with cinematic mood and atmosphere.",
                        "min_price": 200000,
                        "max_price": 700000,
                        "suggested_price": 400000,
                        "estimated_delivery_hours": 24,
                    },
                ],
            },
            {
                "title": "Russian Edit",
                "slug": "russian-edit",
                "description": "Popular Russian-style portrait editing with glossy color and skin look.",
                "sort_order": 3,
                "styles": [
                    {
                        "title": "Russian Portrait",
                        "slug": "russian-portrait",
                        "description": "Glossy portrait retouch with Russian-style color and skin finish.",
                        "min_price": 250000,
                        "max_price": 900000,
                        "suggested_price": 500000,
                        "estimated_delivery_hours": 36,
                    },
                ],
            },
            {
                "title": "Wedding Retouch",
                "slug": "wedding-retouch",
                "description": "Wedding photo editing, skin cleanup, dress detail, color and album consistency.",
                "sort_order": 4,
                "styles": [
                    {
                        "title": "Wedding Basic",
                        "slug": "wedding-basic",
                        "description": "Basic wedding color and light correction.",
                        "min_price": 50000,
                        "max_price": 150000,
                        "suggested_price": 100000,
                        "estimated_delivery_hours": 24,
                    },
                    {
                        "title": "Wedding Premium",
                        "slug": "wedding-premium",
                        "description": "Detailed wedding retouch with skin, dress, background and color work.",
                        "min_price": 200000,
                        "max_price": 800000,
                        "suggested_price": 450000,
                        "estimated_delivery_hours": 48,
                    },
                ],
            },
            {
                "title": "Product Photo",
                "slug": "product-photo",
                "description": "Product cleanup, background removal, shadow, color correction and marketplace-ready output.",
                "sort_order": 5,
                "styles": [
                    {
                        "title": "Background Cleanup",
                        "slug": "background-cleanup",
                        "description": "Remove or clean background and prepare product image.",
                        "min_price": 50000,
                        "max_price": 250000,
                        "suggested_price": 120000,
                        "estimated_delivery_hours": 12,
                    },
                    {
                        "title": "Commercial Product Retouch",
                        "slug": "commercial-product-retouch",
                        "description": "High quality product retouch with cleanup, lighting and color.",
                        "min_price": 250000,
                        "max_price": 1000000,
                        "suggested_price": 550000,
                        "estimated_delivery_hours": 36,
                    },
                ],
            },
        ]

        created_categories = 0
        created_styles = 0
        created_packages = 0

        for category_data in catalog_data:
            styles_data = category_data.pop("styles")

            category, category_created = EditCategory.objects.update_or_create(
                slug=category_data["slug"],
                defaults=category_data,
            )

            if category_created:
                created_categories += 1

            for style_data in styles_data:
                style, style_created = EditStyle.objects.update_or_create(
                    slug=style_data["slug"],
                    defaults={
                        **style_data,
                        "category": category,
                    },
                )

                if style_created:
                    created_styles += 1

                packages = [
                    {
                        "title": "Basic",
                        "level": EditPackage.PackageLevel.BASIC,
                        "description": "Basic edit package for simple needs.",
                        "price": max(style.min_price, 1),
                        "min_images": 1,
                        "max_images": 1,
                        "estimated_delivery_hours": style.estimated_delivery_hours,
                        "revision_count": 1,
                        "sort_order": 1,
                    },
                    {
                        "title": "Standard",
                        "level": EditPackage.PackageLevel.STANDARD,
                        "description": "Balanced package with standard quality and delivery.",
                        "price": style.suggested_price or style.min_price,
                        "min_images": 1,
                        "max_images": 3,
                        "estimated_delivery_hours": style.estimated_delivery_hours,
                        "revision_count": 2,
                        "sort_order": 2,
                    },
                    {
                        "title": "Premium",
                        "level": EditPackage.PackageLevel.PREMIUM,
                        "description": "Premium package with more detail and extra revision.",
                        "price": style.max_price or style.suggested_price or style.min_price,
                        "min_images": 1,
                        "max_images": 5,
                        "estimated_delivery_hours": style.estimated_delivery_hours * 2,
                        "revision_count": 3,
                        "sort_order": 3,
                    },
                ]

                for package_data in packages:
                    package, package_created = EditPackage.objects.update_or_create(
                        style=style,
                        level=package_data["level"],
                        title=package_data["title"],
                        defaults=package_data,
                    )

                    if package_created:
                        created_packages += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Catalog demo data created successfully. "
                f"Categories created: {created_categories}, "
                f"Styles created: {created_styles}, "
                f"Packages created: {created_packages}"
            )
        )