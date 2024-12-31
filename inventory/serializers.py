from rest_framework import serializers
from .models import Category, Product, Supplier, Orders, OrderProduct, Usage, Notification, UsageProduct

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

    def get_product_count(self, obj):
        return obj.product_set.count()

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'short_description', 'price', 'stock', 
            'value', 're_stock_level', 'SKU', 'category', 'category_name',
            'stock_status', 'created_at', 'updated_at'
        ]

    def get_stock_status(self, obj):
        if obj.stock <= 0:
            return "Out of Stock"
        elif obj.stock <= obj.re_stock_level:
            return "Low Stock"
        return "In Stock"

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value

class SupplierSerializer(serializers.ModelSerializer):
    total_orders = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'telephone', 'address', 'created_at', 'total_orders']

    def get_total_orders(self, obj):
        return obj.orders_set.count()

class OrderProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.SKU', read_only=True)
    
    class Meta:
        model = OrderProduct
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'price', 'value']
        
    def validate(self, data):
        if data['quantity'] <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        if data['price'] <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return data

class OrdersSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Orders
        fields = ['id', 'supplier', 'supplier_name', 'order_date', 
                 'total_value', 'status', 'status_display', 'order_products']

    def create(self, validated_data):
        order_products_data = validated_data.pop('order_products')
        order = Orders.objects.create(**validated_data)
        for product_data in order_products_data:
            OrderProduct.objects.create(order=order, **product_data)
        return order

class UsageProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.SKU', read_only=True)
    
    class Meta:
        model = UsageProduct
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'value']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

class UsageSerializer(serializers.ModelSerializer):
    usage_products = UsageProductSerializer(many=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    
    class Meta:
        model = Usage
        fields = ['id', 'usage_type', 'usage_type_display', 'date', 
                 'notes', 'total_value', 'usage_products']

    def create(self, validated_data):
        usage_products_data = validated_data.pop('usage_products')
        usage = Usage.objects.create(**validated_data)
        for product_data in usage_products_data:
            UsageProduct.objects.create(usage=usage, **product_data)
        return usage

class NotificationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'product', 'product_name', 'notification_type', 
                 'notification_type_display', 'message', 'created_at', 'is_read']

    def validate(self, data):
        if data['product'].stock > data['product'].re_stock_level and data['notification_type'] == 'LOW_STOCK':
            raise serializers.ValidationError("Cannot create low stock notification for product with sufficient stock")
        return data

