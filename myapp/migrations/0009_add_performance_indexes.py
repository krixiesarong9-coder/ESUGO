from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_order_payment_method'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_available', 'stock'], name='myapp_produ_is_avai_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['owner', 'is_available'], name='myapp_produ_owner_i_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'is_available'], name='myapp_produ_categor_idx'),
        ),
        migrations.AddIndex(
            model_name='storesettings',
            index=models.Index(fields=['owner'], name='myapp_store_owner_i_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['user_type'], name='myapp_profi_user_ty_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status'], name='myapp_order_status_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_status'], name='myapp_order_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user', '-created_at'], name='myapp_order_user_cr_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['store_owner', 'status'], name='myapp_order_store_s_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['rider', 'status'], name='myapp_order_rider_s_idx'),
        ),
    ]
