from django.contrib import admin
from django.db.models import Prefetch
from .models import (
    DrugCategory, Drug, Supplier, Order, 
    OrderItem, Transaction, Inventory, 
    PriceHistory, Notifications
)

class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category')
    search_fields = ('name', 'description')
    list_filter = ('parent_category',)
    list_select_related = ('parent_category',)

class PriceHistoryInline(admin.TabularInline):
    model = PriceHistory
    extra = 0
    readonly_fields = ('time_created',)
    can_delete = False
    max_num = 10

class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False
    max_num = 1

class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'SKU', 'category', 'dispense_unit')
    search_fields = ('name', 'SKU', 'description')
    list_filter = ('category', 'dispense_unit')
    ordering = ('name',)
    list_select_related = ('category',)
    inlines = [InventoryInline, PriceHistoryInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'SKU', 'category')
        }),
        ('Unit Information', {
            'fields': ('dispense_unit',)
        })
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['drug', 'quantity', 'purchase_price']
    autocomplete_fields = ['drug']

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'status', 'time_created')
    list_filter = ('status', 'time_created')
    search_fields = ('supplier__name',)
    ordering = ('-time_created',)
    inlines = [OrderItemInline]
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

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'telephone', 'email')
    search_fields = ('name', 'contact_person', 'email', 'address')
    ordering = ('name',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('drug', 'transaction_type', 'quantity', 'selling_price', 'time_created')
    list_filter = ('transaction_type', 'time_created')
    search_fields = ('drug__name', 'drug__SKU')
    ordering = ('-time_created',)
    list_select_related = ('drug',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('drug')

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('drug', 'quantity', 'reorder_level', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('drug__name', 'drug__SKU')
    ordering = ('drug__name',)
    list_select_related = ('drug',)

class NotificationsAdmin(admin.ModelAdmin):
    list_display = ('drug', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('drug__name', 'message')
    ordering = ('-created_at',)
    readonly_fields = ['created_at']
    list_select_related = ('drug',)

# Register all models
admin.site.register(DrugCategory, DrugCategoryAdmin)
admin.site.register(Drug, DrugAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Notifications, NotificationsAdmin)
admin.site.register(PriceHistory)
