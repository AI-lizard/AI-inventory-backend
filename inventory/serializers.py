from rest_framework import serializers
from .models import DrugCategory, Drug, Supplier, Order, OrderItem, DrugUsage, Notifications, PriceHistory

class DrugCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = DrugCategory
        fields = ['id', 'name', 'description', 'parent_category', 'subcategories']

    def get_subcategories(self, obj):
        return DrugCategorySerializer(obj.subcategories.all(), many=True).data

class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'drug', 'purchase_price', 'selling_price', 'date_changed']

class DrugSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    current_stock = serializers.IntegerField(read_only=True)
    price_history = PriceHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Drug
        fields = [
            'id', 'name', 'generic_name', 'description', 'category', 
            'category_name', 'storage_unit', 'dispensing_unit', 
            'units_per_storage', 'storage_count', 'loose_units',
            'current_stock', 'reorder_level', 'purchase_price', 
            'selling_price', 'SKU', 'expiry_date', 'created_at', 
            'updated_at', 'price_history', 'is_expired'
        ]
        read_only_fields = ['current_stock', 'is_expired']

    def validate(self, data):
        if data.get('storage_count', 0) < 0:
            raise serializers.ValidationError("Storage count cannot be negative")
        if data.get('loose_units', 0) < 0:
            raise serializers.ValidationError("Loose units cannot be negative")
        if data.get('loose_units', 0) >= data.get('units_per_storage', 1):
            raise serializers.ValidationError("Loose units should be less than units per storage")
        return data

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'telephone', 'email', 
                 'address', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_sku = serializers.CharField(source='drug.SKU', read_only=True)
    total_value = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = OrderItem
        fields = ['id', 'drug', 'drug_name', 'drug_sku', 'quantity', 
                 'price_per_unit', 'total_value']

    def validate(self, data):
        if data['quantity'] <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        if data['price_per_unit'] <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'supplier', 'supplier_name', 'order_date', 
                 'status', 'status_display', 'total_value', 'items']
        read_only_fields = ['total_value']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

class DrugUsageSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_sku = serializers.CharField(source='drug.SKU', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    
    class Meta:
        model = DrugUsage
        fields = ['id', 'drug', 'drug_name', 'drug_sku', 'usage_type', 
                 'usage_type_display', 'quantity', 'unit_price', 
                 'total_value', 'date', 'notes']
        read_only_fields = ['total_value']

    def validate(self, data):
        if data['quantity'] <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        if data['unit_price'] <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        
        # Check if there's enough stock
        if data['drug'].current_stock < data['quantity']:
            raise serializers.ValidationError(
                f"Insufficient stock. Available: {data['drug'].current_stock} "
                f"{data['drug'].dispensing_unit}"
            )
        return data

class NotificationsSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Notifications
        fields = ['id', 'drug', 'drug_name', 'notification_type', 
                 'notification_type_display', 'message', 'created_at', 
                 'is_read']

