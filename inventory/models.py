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

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        DrugCategory, 
        related_name='drugs',
        on_delete=models.PROTECT
    )
    
    # Unit management
    storage_unit = models.CharField(max_length=10, choices=UNIT_TYPES, help_text="How you store it (Box, Vial)")
    dispensing_unit = models.CharField(max_length=10, choices=UNIT_TYPES, help_text="How you dispense it (Tablet, ML)")
    units_per_storage = models.PositiveIntegerField(help_text="e.g., 25 tablets per box, 5ml per vial")
    storage_count = models.PositiveIntegerField(default=0, help_text="Number of full storage units")
    loose_units = models.PositiveIntegerField(default=0, help_text="Remaining dispensing units")
    reorder_level = models.PositiveIntegerField(default=10)

    @property
    def current_stock(self):
        """Calculate total units dynamically."""
        return (self.storage_count * self.units_per_storage) + self.loose_units

    def dispense(self, amount):
        """Dispense units while properly managing storage units"""
        if amount > self.current_stock:
            raise ValidationError(f"Insufficient stock. Only {self.current_stock} {self.dispensing_unit} available")
        
        remaining = self.current_stock - amount
        self.storage_count = remaining // self.units_per_storage
        self.loose_units = remaining % self.units_per_storage
        self.save()

    #Expiry management
    @property
    def is_expired(self):
        """Check if the drug is expired."""
        return self.expiry_date < now().date()

    @classmethod
    def check_expired_drugs(cls):
        """Identify all expired drugs and create notifications."""
        expired_drugs = cls.objects.filter(expiry_date__lt=now().date())
        for drug in expired_drugs:
            Notifications.objects.get_or_create(
                drug=drug,
                notification_type='EXPIRY',
                defaults={
                    'message': f"The drug {drug.name} has expired. Please take necessary actions."
                }
            )
    
    # Stock management
    current_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    
    # Current pricing
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    SKU = models.CharField(max_length=50, unique=True)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.SKU})"

    def check_stock_level(self):
        if self.current_stock <= self.reorder_level:
            Notifications.objects.create_low_stock_alert(self)

class PriceHistory(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='price_history')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_changed = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_changed']

class Supplier(models.Model):
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
        ('ORDERED', 'Ordered'),
        ('PENDING', 'Pending'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_total_value(self):
        """Recalculate the total value of the order."""
        self.total_value = sum(item.total_value for item in self.items.all())
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total_value(self):
        """Calculate the total value for this item."""
        return self.quantity * self.price_per_unit
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.calculate_total_value()
        
        # Update stock when order is received
        if self.status == 'RECEIVED':
            self.drug.current_stock += self.quantity
            self.drug.save()

class DrugUsage(models.Model):
    USAGE_TYPES = [
        ('SALE', 'Sale'),
        ('EXPIRED', 'Expired'),
        ('USED', 'Used'),
        ('DAMAGE', 'Damage'),
    ]
    
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    usage_type = models.CharField(max_length=10, choices=USAGE_TYPES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.drug.current_stock < self.quantity:
            raise ValidationError(f"Insufficient stock. Available: {self.drug.current_stock}")
            
        self.total_value = self.quantity * self.unit_price
        self.drug.current_stock -= self.quantity
        self.drug.save()
        
        super().save(*args, **kwargs)

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
