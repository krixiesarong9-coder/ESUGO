from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


STORE_OWNER_USERNAMES = {'hannastore', 'hedricstore', 'happymart'}


class Command(BaseCommand):
    help = "Delete seeded store owner accounts so they are recreated fresh on next seed."

    def handle(self, *args, **options):
        deleted, _ = User.objects.filter(username__in=STORE_OWNER_USERNAMES).delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {deleted} records for store owner accounts. They will be recreated fresh by load_initial_data_once."
        ))
