# Generated by Django 5.1.3 on 2024-11-08 15:38

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_remove_orderitem_order_remove_orderitem_product_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orders",
            name="price",
        ),
        migrations.RemoveField(
            model_name="orders",
            name="product",
        ),
        migrations.RemoveField(
            model_name="orders",
            name="quantity",
        ),
        migrations.RemoveField(
            model_name="orders",
            name="value",
        ),
        migrations.AddField(
            model_name="orders",
            name="total_value",
            field=models.DecimalField(
                decimal_places=2, default=0, editable=False, max_digits=10
            ),
        ),
        migrations.CreateModel(
            name="OrderProduct",
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
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=2, editable=False, max_digits=10
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_products",
                        to="inventory.orders",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_products",
                        to="inventory.product",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="orders",
            name="products",
            field=models.ManyToManyField(
                related_name="orders",
                through="inventory.OrderProduct",
                to="inventory.product",
            ),
        ),
    ]