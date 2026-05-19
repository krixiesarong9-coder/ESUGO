from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Category, Product, Profile, StoreSettings
import urllib.request
import os
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'Seed the database with sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create categories
        categories_data = [
            {'name': 'Fruits', 'slug': 'fruits', 'description': 'Fresh and juicy fruits'},
            {'name': 'Vegetables', 'slug': 'vegetables', 'description': 'Fresh vegetables and greens'},
            {'name': 'Dairy', 'slug': 'dairy', 'description': 'Milk, cheese, and dairy products'},
            {'name': 'Bakery', 'slug': 'bakery', 'description': 'Fresh bread and baked goods'},
            {'name': 'Meat', 'slug': 'meat', 'description': 'Fresh meat and poultry'},
            {'name': 'Beverages', 'slug': 'beverages', 'description': 'Drinks and beverages'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            categories[cat_data['slug']] = cat
            if created:
                self.stdout.write(f'Created category: {cat.name}')

        # Create products
        products_data = [
            # Fruits
            {'name': 'Fresh Apples', 'slug': 'fresh-apples', 'category': 'fruits', 'price': '3.99', 'stock': 50, 'description': 'Crisp and juicy red apples, perfect for snacking.'},
            {'name': 'Bananas', 'slug': 'bananas', 'category': 'fruits', 'price': '1.99', 'stock': 100, 'description': 'Ripe yellow bananas, rich in potassium.'},
            {'name': 'Oranges', 'slug': 'oranges', 'category': 'fruits', 'price': '4.49', 'stock': 40, 'description': 'Sweet and tangy oranges, great for juice.'},
            {'name': 'Strawberries', 'slug': 'strawberries', 'category': 'fruits', 'price': '5.99', 'stock': 30, 'description': 'Fresh red strawberries, perfect for desserts.'},
            
            # Vegetables
            {'name': 'Carrots', 'slug': 'carrots', 'category': 'vegetables', 'price': '2.49', 'stock': 60, 'description': 'Fresh organic carrots, great for salads.'},
            {'name': 'Broccoli', 'slug': 'broccoli', 'category': 'vegetables', 'price': '3.29', 'stock': 45, 'description': 'Fresh green broccoli, rich in vitamins.'},
            {'name': 'Tomatoes', 'slug': 'tomatoes', 'category': 'vegetables', 'price': '2.99', 'stock': 80, 'description': 'Ripe red tomatoes, perfect for cooking.'},
            {'name': 'Potatoes', 'slug': 'potatoes', 'category': 'vegetables', 'price': '1.99', 'stock': 100, 'description': 'Fresh potatoes, great for any meal.'},
            
            # Dairy
            {'name': 'Whole Milk', 'slug': 'whole-milk', 'category': 'dairy', 'price': '3.49', 'stock': 40, 'description': 'Fresh whole milk, 1 gallon.'},
            {'name': 'Cheddar Cheese', 'slug': 'cheddar-cheese', 'category': 'dairy', 'price': '4.99', 'stock': 25, 'description': 'Aged cheddar cheese, sharp flavor.'},
            {'name': 'Yogurt', 'slug': 'yogurt', 'category': 'dairy', 'price': '5.49', 'stock': 35, 'description': 'Creamy Greek yogurt, high protein.'},
            {'name': 'Eggs', 'slug': 'eggs', 'category': 'dairy', 'price': '4.29', 'stock': 60, 'description': 'Fresh farm eggs, dozen.'},
            
            # Bakery
            {'name': 'Whole Wheat Bread', 'slug': 'whole-wheat-bread', 'category': 'bakery', 'price': '3.99', 'stock': 30, 'description': 'Freshly baked whole wheat bread.'},
            {'name': 'Croissants', 'slug': 'croissants', 'category': 'bakery', 'price': '6.99', 'stock': 20, 'description': 'Buttery French croissants, pack of 4.'},
            
            # Meat
            {'name': 'Fresh Chicken', 'slug': 'fresh-chicken', 'category': 'meat', 'price': '8.99', 'stock': 40, 'description': 'Fresh whole chicken, perfect for roasting or grilling.'},
            {'name': 'Chicken Breast', 'slug': 'chicken-breast', 'category': 'meat', 'price': '10.99', 'stock': 35, 'description': 'Boneless, skinless chicken breast, lean and tender.'},
            {'name': 'Pork Chop', 'slug': 'pork-chop', 'category': 'meat', 'price': '9.49', 'stock': 30, 'description': 'Juicy pork chops, great for pan-frying or grilling.'},
            {'name': 'Ground Pork', 'slug': 'ground-pork', 'category': 'meat', 'price': '7.99', 'stock': 25, 'description': 'Fresh ground pork, ideal for meatballs, sausages, and cooking.'},
            
            # Beverages
            {'name': 'Orange Juice', 'slug': 'orange-juice', 'category': 'beverages', 'price': '4.99', 'stock': 35, 'description': 'Fresh squeezed orange juice, 1 liter.'},
            {'name': 'Coffee Beans', 'slug': 'coffee-beans', 'category': 'beverages', 'price': '12.99', 'stock': 20, 'description': 'Premium Arabica coffee beans, 1 lb.'},
            {'name': 'Mineral Water', 'slug': 'mineral-water', 'category': 'beverages', 'price': '1.99', 'stock': 100, 'description': 'Natural mineral water, 1 liter.'},
        ]

        # Product image mapping - using loremflickr.com with food keywords for relevant images
        product_images = {
            'fresh-apples': 'https://loremflickr.com/300/200/apple,fruit?lock=12345',
            'bananas': 'https://loremflickr.com/300/200/banana,fruit?lock=12346',
            'oranges': 'https://loremflickr.com/300/200/orange,fruit?lock=12347',
            'strawberries': 'https://loremflickr.com/300/200/strawberry,fruit?lock=12348',
            'carrots': 'https://loremflickr.com/300/200/carrot,vegetable?lock=12349',
            'broccoli': 'https://loremflickr.com/300/200/broccoli,vegetable?lock=12350',
            'tomatoes': 'https://loremflickr.com/300/200/tomato,vegetable?lock=12351',
            'potatoes': 'https://loremflickr.com/300/200/potato,vegetable?lock=12352',
            'whole-milk': 'https://loremflickr.com/300/200/milk,dairy?lock=12353',
            'cheddar-cheese': 'https://loremflickr.com/300/200/cheese,dairy?lock=12354',
            'greek-yogurt': 'https://loremflickr.com/300/200/yogurt,dairy?lock=12355',
            'eggs': 'https://loremflickr.com/300/200/eggs,food?lock=12356',
            'whole-wheat-bread': 'https://loremflickr.com/300/200/bread,bakery?lock=12357',
            'croissants': 'https://loremflickr.com/300/200/croissant,bakery?lock=12358',
            'bagels': 'https://loremflickr.com/300/200/bagel,bakery?lock=12359',
            'orange-juice': 'https://loremflickr.com/300/200/orange-juice,beverage?lock=12360',
            'coffee-beans': 'https://loremflickr.com/300/200/coffee-beans,beverage?lock=12361',
            'mineral-water': 'https://loremflickr.com/300/200/water,bottle?lock=12362',
            'fresh-chicken': 'https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=300&h=200&fit=crop',
            'chicken-breast': 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300&h=200&fit=crop',
            'pork-chop': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=300&h=200&fit=crop',
            'ground-pork': 'https://loremflickr.com/300/200/ground-pork,meat?lock=12366',
        }

        for prod_data in products_data:
            category = categories[prod_data['category']]
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={
                    'name': prod_data['name'],
                    'category': category,
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'stock': prod_data['stock'],
                    'is_available': True
                }
            )
            if created:
                # Download and save product image
                image_url = product_images.get(prod_data['slug'])
                if image_url:
                    try:
                        # Use a simple approach - just save a placeholder with the product name
                        # since we can't guarantee external URLs will work
                        img_filename = f"{prod_data['slug']}.jpg"
                        img_path = os.path.join('products', img_filename)
                        
                        # Try to download the image
                        try:
                            req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=5) as response:
                                image_content = response.read()
                                product.image.save(img_filename, ContentFile(image_content), save=True)
                                self.stdout.write(f'  Downloaded image for: {product.name}')
                        except Exception as e:
                            self.stdout.write(f'  Could not download image for {product.name}: {e}')
                    except Exception as e:
                        self.stdout.write(f'  Error saving image for {product.name}: {e}')
                
                self.stdout.write(f'Created product: {product.name}')

        # Create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': False
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user: testuser / password123'))

        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@esugo.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))

        # Create sample store owners and public store details
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
                }
            )
            if created:
                store_owner.set_password('password123')
                store_owner.save()
                self.stdout.write(self.style.SUCCESS(f"Created store owner: {store_data['username']} / password123"))

            Profile.objects.update_or_create(
                user=store_owner,
                defaults={'user_type': 'store_owner'}
            )
            StoreSettings.objects.update_or_create(
                owner=store_owner,
                defaults={
                    'store_name': store_data['store_name'],
                    'location': store_data['location'],
                    'opening_hours': store_data['opening_hours'],
                }
            )
            store_owners.append(store_owner)

        ownerless_products = Product.objects.filter(owner__isnull=True).order_by('name')
        for index, product in enumerate(ownerless_products):
            product.owner = store_owners[index % len(store_owners)]
            product.save(update_fields=['owner'])

        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
        self.stdout.write(self.style.WARNING('Test user: testuser / password123'))
        self.stdout.write(self.style.WARNING('Admin user: admin / admin123'))
