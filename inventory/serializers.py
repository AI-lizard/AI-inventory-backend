from rest_framework import serializers
from .models import (
    DrugCategory, Drug, Supplier, Order, 
    OrderItem, Transaction, Inventory, 
    PriceHistory, Notifications
)

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
        fields = ['id', 'drug', 'purchase_price', 'time_created']

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'drug', 'quantity', 'reorder_level', 
                 'time_created', 'last_updated']

class DrugSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    inventory = InventorySerializer(read_only=True)
    price_history = PriceHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Drug
        fields = ['id', 'name', 'description', 'SKU', 'category', 
                 'category_name', 'dispense_unit', 'inventory', 
                 'price_history']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'telephone', 
                 'email', 'address', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_sku = serializers.CharField(source='drug.SKU', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'drug', 'drug_name', 'drug_sku', 
                 'quantity', 'purchase_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'supplier', 'supplier_name', 'status', 
                 'status_display', 'time_created', 'items']

    def create(self, validated_data):
        items_data = self.context['request'].data.get('items', [])
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

class TransactionSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_sku = serializers.CharField(source='drug.SKU', read_only=True)
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = ['id', 'drug', 'drug_name', 'drug_sku', 
                 'transaction_type', 'transaction_type_display',
                 'quantity', 'selling_price', 'time_created']

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

