from django.contrib import admin
from django.db.models import Prefetch
from .models import DrugCategory, Drug, Supplier, Order, OrderItem, DrugUsage, Notifications, PriceHistory

class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'SKU', 'storage_count', 'loose_units', 'current_stock', 'category', 'expiry_date')
    search_fields = ('name', 'generic_name', 'SKU')
    list_filter = ('category', 'storage_unit', 'dispensing_unit')
    ordering = ('name',)
    list_select_related = ('category',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'generic_name', 'SKU', 'description', 'category')
        }),
        ('Unit Management', {
            'fields': ('storage_unit', 'dispensing_unit', 'units_per_storage', 
                      'storage_count', 'loose_units', 'reorder_level')
        }),
        ('Pricing', {
            'fields': ('purchase_price', 'selling_price')
        }),
        ('Dates', {
            'fields': ('expiry_date',)
        })
    )
    readonly_fields = ('current_stock',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

class PriceHistoryInline(admin.TabularInline):
    model = PriceHistory
    extra = 0
    readonly_fields = ('date_changed',)
    can_delete = False
    max_num = 10

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['drug', 'quantity', 'price_per_unit', 'total_value']
    readonly_fields = ['total_value']
    autocomplete_fields = ['drug']
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'status', 'total_value', 'order_date')
    list_filter = ('status', 'order_date', 'supplier')
    search_fields = ('supplier__name', 'items__drug__name')
    ordering = ('-order_date',)
    inlines = [OrderItemInline]
    readonly_fields = ['total_value']
    list_select_related = ('supplier',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('supplier')
            .prefetch_related(
                Prefetch(
                    'items',
                    queryset=OrderItem.objects.select_related('drug')
                )
            )
        )

class DrugUsageAdmin(admin.ModelAdmin):
    list_display = ('drug', 'usage_type', 'quantity', 'total_value', 'date')
    list_filter = ('usage_type', 'date')
    search_fields = ('drug__name', 'notes')
    ordering = ('-date',)
    fields = ['drug', 'usage_type', 'quantity', 'unit_price', 'total_value', 'notes']
    readonly_fields = ['total_value']
    autocomplete_fields = ['drug']
    list_select_related = ('drug',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('drug')

class NotificationsAdmin(admin.ModelAdmin):
    list_display = ('drug', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('drug__name', 'message')
    ordering = ('-created_at',)
    readonly_fields = ['created_at']
    list_select_related = ('drug',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('drug')

class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category')
    search_fields = ('name', 'description')
    list_filter = ('parent_category',)
    list_select_related = ('parent_category',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_category')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'telephone', 'email')
    search_fields = ('name', 'contact_person', 'email')
    ordering = ('name',)

# Register all models with optimized admin classes
admin.site.register(DrugCategory, DrugCategoryAdmin)
admin.site.register(Drug, DrugAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(DrugUsage, DrugUsageAdmin)
admin.site.register(Notifications, NotificationsAdmin)
admin.site.register(PriceHistory)  # Add this if you want to manage price history
