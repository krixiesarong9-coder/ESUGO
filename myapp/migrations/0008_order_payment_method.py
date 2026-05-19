from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_order_checkout_url_order_paymongo_link_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('cod', 'Cash on Delivery'),
                    ('paymongo', 'PayMongo'),
                ],
                default='cod',
                max_length=20,
            ),
        ),
    ]
