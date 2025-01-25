from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta
from .models import (
    DrugCategory, Drug, Supplier, Order, 
    OrderItem, Transaction, Inventory, 
    PriceHistory, Notifications
)
from .serializers import (
    DrugCategorySerializer, DrugSerializer, SupplierSerializer,
    OrderSerializer, OrderItemSerializer, TransactionSerializer,
    InventorySerializer, PriceHistorySerializer, NotificationsSerializer
)

class DrugCategoryViewSet(viewsets.ModelViewSet):
    queryset = DrugCategory.objects.all()
    serializer_class = DrugCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @action(detail=True, methods=['get'])
    def drugs(self, request, pk=None):
        category = self.get_object()
        drugs = Drug.objects.filter(category=category)
        serializer = DrugSerializer(drugs, many=True)
        return Response(serializer.data)

class DrugViewSet(viewsets.ModelViewSet):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'dispense_unit']
    search_fields = ['name', 'SKU', 'description']
    ordering_fields = ['name', 'SKU']

    def get_queryset(self):
        return Drug.objects.select_related('category').prefetch_related(
            'inventory', 'price_history'
        )

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['drug']
    ordering_fields = ['quantity', 'last_updated']

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock = Inventory.objects.filter(
            quantity__lte=Q(reorder_level)
        ).select_related('drug')
        serializer = self.get_serializer(low_stock, many=True)
        return Response(serializer.data)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'contact_person', 'email', 'telephone']

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        supplier = self.get_object()
        orders = Order.objects.filter(supplier=supplier)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    ordering_fields = ['time_created']

    def get_queryset(self):
        return Order.objects.select_related('supplier').prefetch_related('items__drug')

    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_orders = self.get_queryset().filter(
            time_created__gte=now() - timedelta(days=30)
        ).order_by('-time_created')
        serializer = self.get_serializer(recent_orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = new_status
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'drug']
    ordering_fields = ['quantity', 'purchase_price']

    def get_queryset(self):
        return OrderItem.objects.select_related('order', 'drug')

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['drug', 'transaction_type']
    ordering_fields = ['time_created']

    def get_queryset(self):
        return Transaction.objects.select_related('drug')

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transactions = self.get_queryset().filter(
            time_created__range=[start_date, end_date]
        )
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PriceHistorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['drug']
    ordering_fields = ['time_created']

    def get_queryset(self):
        return PriceHistory.objects.select_related('drug').order_by('-time_created')

class NotificationsViewSet(viewsets.ModelViewSet):
    queryset = Notifications.objects.all()
    serializer_class = NotificationsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_read', 'notification_type']
    
    def get_queryset(self):
        return Notifications.objects.select_related('drug')

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
