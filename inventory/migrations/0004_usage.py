# Generated by Django 5.1.3 on 2024-11-20 14:02

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_remove_orders_price_remove_orders_product_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Usage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                (
                    "usage_type",
                    models.CharField(
                        choices=[("VET", "Veterinary Use"), ("SALE", "Sale to Owner")],
                        default="VET",
                        max_length=4,
                    ),
                ),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=2, editable=False, max_digits=10
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="usages",
                        to="inventory.product",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Usages",
            },
        ),
    ]
