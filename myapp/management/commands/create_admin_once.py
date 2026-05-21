import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from myapp.models import Profile


class Command(BaseCommand):
    help = "Create the admin superuser once if it does not already exist."

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not password:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_PASSWORD not set — skipping admin creation.'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f'Admin user "{username}" already exists — skipping.'
            ))
            return

        user = User.objects.create_superuser(username=username, email=email, password=password)
        Profile.objects.get_or_create(user=user, defaults={'user_type': 'admin'})
        self.stdout.write(self.style.SUCCESS(
            f'Admin user "{username}" created successfully.'
        ))
