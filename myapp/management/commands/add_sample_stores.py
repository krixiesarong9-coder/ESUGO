from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from myapp.models import Product, Profile, StoreSettings


class Command(BaseCommand):
    help = 'Add sample stores for customers to choose from'

    def handle(self, *args, **kwargs):
        stores_data = [
            {
                'username': 'hanna_store',
                'email': 'hanna@esugo.com',
                'first_name': 'Hanna',
                'last_name': 'Store',
                'store_name': 'Hanna Store',
                'location': 'Main Street, Barangay Centro',
                'opening_hours': '8:00 AM - 8:00 PM',
            },
            {
                'username': 'hedric_store',
                'email': 'hedric@esugo.com',
                'first_name': 'Hedric',
                'last_name': 'Store',
                'store_name': 'Hedric Store',
                'location': 'Market Road, Barangay San Jose',
                'opening_hours': '7:00 AM - 9:00 PM',
            },
            {
                'username': 'happy_mart',
                'email': 'happy@esugo.com',
                'first_name': 'Happy',
                'last_name': 'Mart',
                'store_name': 'Happy Mart',
                'location': 'Rizal Avenue, Barangay Poblacion',
                'opening_hours': '8:00 AM - 10:00 PM',
            },
        ]

        store_owners = []
        for store_data in stores_data:
            store_owner, created = User.objects.get_or_create(
                username=store_data['username'],
                defaults={
                    'email': store_data['email'],
                    'first_name': store_data['first_name'],
                    'last_name': store_data['last_name'],
                    'is_staff': False,
                },
            )
            if created:
                store_owner.set_password('password123')
                store_owner.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {store_data['username']} / password123"))

            Profile.objects.update_or_create(
                user=store_owner,
                defaults={'user_type': 'store_owner'},
            )
            StoreSettings.objects.update_or_create(
                owner=store_owner,
                defaults={
                    'store_name': store_data['store_name'],
                    'location': store_data['location'],
                    'opening_hours': store_data['opening_hours'],
                },
            )
            store_owners.append(store_owner)
            self.stdout.write(self.style.SUCCESS(f"Added store: {store_data['store_name']}"))

        ownerless_products = Product.objects.filter(owner__isnull=True).order_by('name')
        assigned_count = 0
        for index, product in enumerate(ownerless_products):
            product.owner = store_owners[index % len(store_owners)]
            product.save(update_fields=['owner'])
            assigned_count += 1

        self.stdout.write(self.style.SUCCESS(f'Assigned {assigned_count} ownerless products to sample stores.'))
