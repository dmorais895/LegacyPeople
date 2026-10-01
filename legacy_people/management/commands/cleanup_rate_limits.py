"""Remove expired counters without resetting active request quotas."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from legacy_people.models import RateLimit


class Command(BaseCommand):
    help = "Deletes expired rate-limit counters; schedule periodically for housekeeping."

    def handle(self, *args, **options):
        deleted, _ = RateLimit.objects.filter(expires_at__lte=timezone.now()).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired rate-limit counters."))
