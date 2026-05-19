from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from myapp.models import Product
from django.db.models import Q
import urllib.request
import os


class Command(BaseCommand):
    help = 'Update product image by product name or slug'

    def add_arguments(self, parser):
        parser.add_argument('product_identifier', type=str, nargs='?', default=None, help='Product name or slug')
        parser.add_argument('--image-url', type=str, help='URL of the new image (optional - will use default if not provided)')
        parser.add_argument('--image-file', type=str, help='Local path to image file (optional)')
        parser.add_argument('--list', action='store_true', help='List all products with their current images')

    def handle(self, *args, **options):
        if options['list'] or options['product_identifier'] is None:
            self.list_products()
            return

        product_identifier = options['product_identifier']
        image_url = options['image_url']
        image_file = options['image_file']

        # Find the product by name or slug
        try:
            product = Product.objects.get(
                Q(name__iexact=product_identifier) | Q(slug=product_identifier)
            )
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Product "{product_identifier}" not found!'))
            self.list_products()
            return
        except Product.MultipleObjectsReturned:
            self.stderr.write(self.style.ERROR(f'Multiple products found for "{product_identifier}". Use the exact slug:'))
            products = Product.objects.filter(
                Q(name__iexact=product_identifier) | Q(slug=product_identifier)
            )
            for p in products:
                self.stderr.write(f'  - {p.name} (slug: {p.slug})')
            return

        self.stdout.write(f'Found product: {product.name} (ID: {product.id})')
        self.stdout.write(f'Current image: {product.image if product.image else "None"}')
        old_image = str(product.image) if product.image else None

        # Update the image
        if image_file:
            # Use local file
            if os.path.exists(image_file):
                self.stdout.write(f'Downloading image from file: {image_file}')
                with open(image_file, 'rb') as f:
                    filename = os.path.basename(image_file)
                    product.image.save(filename, ContentFile(f.read()), save=True)
                self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated image from file: {image_file}'))
                self.stdout.write(f'New image: {product.image}')
            else:
                self.stderr.write(self.style.ERROR(f'File not found: {image_file}'))
        elif image_url:
            # Download from URL
            self.stdout.write(f'Downloading image from URL: {image_url}')
            try:
                req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    image_content = response.read()
                    self.stdout.write(f'Downloaded {len(image_content)} bytes')
                    filename = f'{product.slug}.jpg'
                    product.image.save(filename, ContentFile(image_content), save=True)
                self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated image from URL: {image_url}'))
                self.stdout.write(f'New image: {product.image}')
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to download image: {e}'))
                import traceback
                self.stderr.write(traceback.format_exc())
        else:
            # Use default loremflickr image based on product category
            default_images = {
                'fresh-apples': 'https://loremflickr.com/600/400/apple,fruit?lock=12346',
                'bananas': 'https://loremflickr.com/600/400/banana,fruit?lock=12347',
                'oranges': 'https://loremflickr.com/600/400/orange,fruit?lock=12348',
                'strawberries': 'https://loremflickr.com/600/400/strawberry,fruit?lock=12349',
                'carrots': 'https://loremflickr.com/600/400/carrot,vegetable?lock=12350',
                'broccoli': 'https://loremflickr.com/600/400/broccoli,vegetable?lock=12351',
                'tomatoes': 'https://loremflickr.com/600/400/tomato,vegetable?lock=12352',
                'potatoes': 'https://loremflickr.com/600/400/potato,vegetable?lock=12353',
                'whole-milk': 'https://loremflickr.com/600/400/milk,dairy?lock=12354',
                'cheddar-cheese': 'https://loremflickr.com/600/400/cheese,dairy?lock=12355',
                'greek-yogurt': 'https://loremflickr.com/600/400/yogurt,dairy?lock=12356',
                'eggs': 'https://loremflickr.com/600/400/eggs,food?lock=12357',
                'whole-wheat-bread': 'https://loremflickr.com/600/400/bread,bakery?lock=12358',
                'croissants': 'https://loremflickr.com/600/400/croissant,bakery?lock=12359',
                'bagels': 'https://loremflickr.com/600/400/bagel,bakery?lock=12360',
                'orange-juice': 'https://loremflickr.com/600/400/orange-juice,beverage?lock=12361',
                'coffee-beans': 'https://loremflickr.com/600/400/coffee-beans,beverage?lock=12362',
                'mineral-water': 'https://loremflickr.com/600/400/water,bottle?lock=12363',
            }

            url = default_images.get(product.slug)
            if url:
                self.stdout.write(f'Downloading default image from URL: {url}')
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        image_content = response.read()
                        self.stdout.write(f'Downloaded {len(image_content)} bytes')
                        filename = f'{product.slug}.jpg'
                        product.image.save(filename, ContentFile(image_content), save=True)
                    self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated image with default image'))
                    self.stdout.write(f'New image: {product.image}')
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Failed to download default image: {e}'))
                    import traceback
                    self.stderr.write(traceback.format_exc())
            else:
                self.stderr.write(self.style.ERROR(f'No default image available for this product. Please provide --image-url or --image-file'))
                self.stdout.write(self.style.SUCCESS(f'\n{current_category}:'))
            
            image_status = '✓' if product.image else '✗'
            self.stdout.write(f'  [{image_status}] {product.name} (slug: {product.slug})')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('\nUsage examples:')
        self.stdout.write('  python manage.py update_product_image "Bananas" --list')
        self.stdout.write('  python manage.py update_product_image "Bananas"')
        self.stdout.write('  python manage.py update_product_image bananas --image-url "https://example.com/banana.jpg"')
        self.stdout.write('  python manage.py update_product_image bananas --image-file "/path/to/banana.jpg"')