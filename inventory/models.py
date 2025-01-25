from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now

class DrugCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subcategories'
    )
    
    class Meta:
        verbose_name_plural = "Drug Categories"
        
    def __str__(self):
        return self.name

class Drug(models.Model):
    UNIT_TYPES = [
        ('TABLET', 'Tablets'),
        ('ML', 'Milliliters'),
        ('BOX', 'Boxes'),
        ('VIAL', 'Vials'),
    ]
    
    # Foreign Key
    category = models.ForeignKey(
        DrugCategory, 
        related_name='drugs',
        on_delete=models.PROTECT
    )
    
    # Basic Information as per ERD
    name = models.CharField(max_length=200)
    description = models.TextField()
    SKU = models.CharField(max_length=50, unique=True)
    dispense_unit = models.CharField(
        max_length=10, 
        choices=UNIT_TYPES
    )

    def __str__(self):
        return f"{self.name} ({self.SKU})"

class PriceHistory(models.Model):
    # Foreign Key
    drug = models.ForeignKey(
        Drug, 
        on_delete=models.CASCADE, 
        related_name='price_history'
    )
    
    # Basic Information as per ERD
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="The cost at that point in history"
    )
    time_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-time_created']
        verbose_name_plural = "Price Histories"

    def __str__(self):
        return f"Price history for {self.drug.name} - {self.time_created.date()}"

class Supplier(models.Model):
    # Basic Information as per ERD
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('PLACED', 'Placed'),
        ('IN_PROGRESS', 'In Progress'),
        ('RECEIVED', 'Received')
    ]
    
    # Foreign Key
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT
    )
    
    # Basic Information as per ERD
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PLACED'
    )
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.supplier.name}"

class OrderItem(models.Model):
    # Foreign Keys as per ERD
    order = models.ForeignKey(
        Order, 
        related_name='items', 
        on_delete=models.CASCADE
    )
    drug = models.ForeignKey(
        Drug, 
        on_delete=models.PROTECT
    )
    
    # Basic Information as per ERD
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Unit cost at time of order"
    )

    def __str__(self):
        return f"Order {self.order.id} - {self.drug.name} ({self.quantity})"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('USAGE', 'Usage')
    ]
    
    # Foreign Key as per ERD
    drug = models.ForeignKey(
        Drug, 
        on_delete=models.PROTECT
    )
    
    # Basic Information as per ERD
    transaction_type = models.CharField(
        max_length=10, 
        choices=TRANSACTION_TYPES
    )
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Only applicable for sales"
    )
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.drug.name} ({self.quantity})"

class Notifications(models.Model):
    NOTIFICATION_TYPES = [
        ('LOW_STOCK', 'Low Stock Alert'),
        ('EXPIRY', 'Expiry Alert'),
    ]
    
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    @classmethod
    def create_low_stock_alert(cls, drug):
        if not cls.objects.filter(
            drug=drug,
            notification_type='LOW_STOCK',
            is_read=False
        ).exists():
            message = f"Low stock alert for {drug.name}. Current stock: {drug.current_stock}"
            cls.objects.create(
                drug=drug,
                notification_type='LOW_STOCK',
                message=message
            )
            # Send email notification
            send_mail(
                subject=f'Low Stock Alert - {drug.name}',
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )

class Inventory(models.Model):
    # Foreign Key - One-to-One relationship with Drug
    drug = models.OneToOneField(
        Drug,
        on_delete=models.PROTECT,
        related_name='inventory'
    )
    
    # Basic Information as per ERD
    quantity = models.PositiveIntegerField(
        help_text="Current stock on hand"
    )
    reorder_level = models.PositiveIntegerField(
        help_text="Threshold at which an alert or reorder is triggered"
    )
    time_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventories"

    def __str__(self):
        return f"Inventory for {self.drug.name}"