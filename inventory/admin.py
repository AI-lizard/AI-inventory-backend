from django.contrib import admin
from .models import Category, Product, Supplier, Orders, OrderProduct, Usage, Notification, UsageProduct

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'SKU', 'price', 'stock', 'category')
    search_fields = ('name', 'SKU')
    list_filter = ('category',)
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'SKU', 'category')
        }),
        ('Pricing and Stock', {
            'fields': ('price', 'stock', 're_stock_level')
        }),
    )

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1
    fields = ['product', 'quantity', 'price', 'value']
    readonly_fields = ['value']

class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'total_value', 'order_date')
    list_filter = ('supplier', 'order_date')
    search_fields = ('supplier__name', 'order_products__product__name')
    ordering = ('-order_date',)
    inlines = [OrderProductInline]

class UsageProductInline(admin.TabularInline):
    model = UsageProduct
    extra = 1
    fields = ['product', 'quantity', 'value']
    readonly_fields = ['value']

class UsageAdmin(admin.ModelAdmin):
    list_display = ('id', 'usage_type', 'date', 'total_value')
    list_filter = ('usage_type', 'date')
    search_fields = ('notes', 'usage_products__product__name')
    ordering = ('-date',)
    readonly_fields = ['total_value']
    inlines = [UsageProductInline]

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'product', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('product__name', 'message')
    ordering = ('-created_at',)

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Supplier)
admin.site.register(Orders, OrdersAdmin)
admin.site.register(Usage, UsageAdmin)
admin.site.register(Notification, NotificationAdmin)
