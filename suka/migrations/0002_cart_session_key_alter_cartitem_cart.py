# Generated by Django 5.1.3 on 2024-11-14 15:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suka', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='session_key',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='suka.cart'),
        ),
    ]
