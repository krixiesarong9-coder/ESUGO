# Generated manually for store owner order approval flow

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_product_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='store_owner',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'profile__user_type': 'store_owner'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='store_orders',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
