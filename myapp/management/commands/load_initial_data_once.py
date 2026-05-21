import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import BaseCommand

from myapp.models import Category, Product, Profile, StoreSettings


class Command(BaseCommand):
    help = "Seed the public stores and products without touching live customer accounts."

    store_owner_usernames = {"hannastore", "hedricstore", "happymart"}

    def handle(self, *args, **options):
        existing_count = User.objects.filter(username__in=self.store_owner_usernames).count()
        if existing_count >= len(self.store_owner_usernames):
            self.stdout.write(self.style.WARNING("Initial data skipped: store owner accounts already exist."))
            return

        fixture_path = settings.BASE_DIR / "fixtures" / "initial_data.json"
        with fixture_path.open(encoding="utf-8") as fixture_file:
            objects = json.load(fixture_file)

        users = {}
        for item in objects:
            if item["model"] != "auth.user":
                continue

            fields = item["fields"]
            username = fields["username"]
            if username not in self.store_owner_usernames:
                continue

            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "password": fields["password"],
                    "first_name": fields["first_name"],
                    "last_name": fields["last_name"],
                    "email": fields["email"],
                    "is_staff": fields["is_staff"],
                    "is_superuser": fields["is_superuser"],
                    "is_active": fields["is_active"],
                },
            )
            users[username] = user

        for username, user in users.items():
            Profile.objects.update_or_create(
                user=user,
                defaults={"user_type": "store_owner"},
            )

        categories_by_pk = {}
        for item in objects:
            if item["model"] != "myapp.category":
                continue

            fields = item["fields"]
            category, _ = Category.objects.update_or_create(
                slug=fields["slug"],
                defaults={
                    "name": fields["name"],
                    "description": fields["description"],
                    "image": fields["image"],
                },
            )
            categories_by_pk[item["pk"]] = category

        for item in objects:
            if item["model"] != "myapp.storesettings":
                continue

            fields = item["fields"]
            username = fields["owner"][0]
            owner = users.get(username)
            if not owner:
                continue

            StoreSettings.objects.update_or_create(
                owner=owner,
                defaults={
                    "store_name": fields["store_name"],
                    "location": fields["location"],
                    "opening_hours": fields["opening_hours"],
                },
            )

        seeded_products = 0
        for item in objects:
            if item["model"] != "myapp.product":
                continue

            fields = item["fields"]
            owner_ref = fields["owner"]
            if not owner_ref:
                continue

            owner = users.get(owner_ref[0])
            category = categories_by_pk.get(fields["category"])
            if not owner or not category:
                continue

            Product.objects.update_or_create(
                slug=fields["slug"],
                defaults={
                    "owner": owner,
                    "name": fields["name"],
                    "category": category,
                    "description": fields["description"],
                    "price": fields["price"],
                    "stock": fields["stock"],
                    "image": fields["image"],
                    "is_available": fields["is_available"],
                },
            )
            seeded_products += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(users)} stores and {seeded_products} products from fixtures/initial_data.json."
        ))
