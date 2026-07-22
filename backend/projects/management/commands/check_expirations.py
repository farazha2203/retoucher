"""
Management command to manually check expirations.

Usage:
    python manage.py check_expirations
    python manage.py check_expirations --requests-only
    python manage.py check_expirations --proposals-only
"""
from django.core.management.base import BaseCommand, CommandError
from projects.expiration_handler import ProjectExpirationHandler


class Command(BaseCommand):
    help = "Check and process expired project requests and proposals"

    def add_arguments(self, parser):
        parser.add_argument(
            '--requests-only',
            action='store_true',
            help='Only check project request expirations',
        )
        parser.add_argument(
            '--proposals-only',
            action='store_true',
            help='Only check proposal deadlines',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        requests_only = options.get('requests_only', False)
        proposals_only = options.get('proposals_only', False)
        dry_run = options.get('dry_run', False)

        if not requests_only and not proposals_only:
            # Run both
            requests_only = True
            proposals_only = True

        if requests_only:
            self.stdout.write("Checking project request expirations...")
            try:
                expired_count = ProjectExpirationHandler.check_and_expire_requests()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Processed {expired_count} expired project requests"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))

        if proposals_only:
            self.stdout.write("Checking proposal deadlines...")
            try:
                rejected_count = ProjectExpirationHandler.check_and_reject_proposals()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Auto-rejected {rejected_count} proposals"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))