from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    short_description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.PositiveIntegerField(default=0)
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        editable=False
    )  # Calculated field: price * stock
    re_stock_level = models.PositiveIntegerField(default=10)
    SKU = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(
        Category, 
        related_name='products',
        on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_stock_level(self):
        """Check if stock is at or below re_stock_level and create notification if needed"""
        if self.stock <= self.re_stock_level:
            # Create notification if one doesn't exist for this low stock event
            if not Notification.objects.filter(
                product=self,
                notification_type='LOW_STOCK',
                is_read=False
            ).exists():
                message = f"Product '{self.name}' stock is running low. Current stock: {self.stock}. Restock level: {self.re_stock_level}"
                
                # Create notification
                notification = Notification.objects.create(
                    product=self,
                    notification_type='LOW_STOCK',
                    message=message
                )
                
                # Send email
                send_mail(
                    subject=f'Low Stock Alert - {self.name}',
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True,
                )
                
                return notification
        return None

    def save(self, *args, **kwargs):
        self.value = self.price * self.stock
        super().save(*args, **kwargs)
        self.check_stock_level()  # Check stock level after saving

    def __str__(self):
        return f"{self.name} ({self.SKU})"

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Orders(models.Model):
    supplier = models.ForeignKey(
        Supplier, 
        related_name='orders',
        on_delete=models.PROTECT
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        editable=False
    )
    products = models.ManyToManyField(
        Product,
        through='OrderProduct',
        related_name='orders'
    )

    class Meta:
        verbose_name_plural = "Orders"

    def update_total_value(self):
        self.total_value = sum(item.value for item in self.order_products.all())
        self.save()

    def __str__(self):
        return f"Order {self.id} - {self.supplier.name}"

class OrderProduct(models.Model):
    order = models.ForeignKey(
        Orders,
        related_name='order_products',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='order_products',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    def save(self, *args, **kwargs):
        self.value = self.price * self.quantity
        
        # Get the product's current stock before saving
        if not self.pk:  # Only for new orders (not updates)
            product = self.product
            product.stock += self.quantity  # Add to stock since it's a purchase order
            product.save()
            
        super().save(*args, **kwargs)
        self.order.update_total_value()

    def delete(self, *args, **kwargs):
        # Revert stock changes when order item is deleted
        self.product.stock -= self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"
    

class Usage(models.Model):
    USAGE_TYPES = [
        ('VET', 'Veterinary Use'),
        ('SALE', 'Sale to Owner')
    ]
    
    usage_type = models.CharField(max_length=4, choices=USAGE_TYPES, default='VET')
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    total_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        editable=False
    )
    products = models.ManyToManyField(
        Product,
        through='UsageProduct',
        related_name='usage_sessions'
    )

    class Meta:
        verbose_name_plural = "Usages"

    def update_total_value(self):
        self.total_value = sum(item.value for item in self.usage_products.all())
        self.save()

    def __str__(self):
        return f"Usage {self.id} - {self.get_usage_type_display()} - {self.date}"

class UsageProduct(models.Model):
    usage = models.ForeignKey(
        Usage,
        related_name='usage_products',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='usage_products',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    def save(self, *args, **kwargs):
        if not self.pk:  # Only for new usage records
            if self.product.stock < self.quantity:
                raise ValidationError(
                    f"Insufficient stock for {self.product.name}. "
                    f"Available: {self.product.stock}, Requested: {self.quantity}"
                )
            
            # Calculate value and update product stock
            self.value = self.product.price * self.quantity
            self.product.stock -= self.quantity
            self.product.save()
            
        super().save(*args, **kwargs)
        self.usage.update_total_value()

    def delete(self, *args, **kwargs):
        # Restore stock when usage product is deleted
        self.product.stock += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('LOW_STOCK', 'Low Stock Alert'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.notification_type} - {self.product.name}"

