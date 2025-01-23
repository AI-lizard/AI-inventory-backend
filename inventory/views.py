from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta
from .models import DrugCategory, Drug, Supplier, Order, OrderItem, DrugUsage, Notifications, PriceHistory
from .serializers import (
    DrugCategorySerializer, DrugSerializer, SupplierSerializer,
    OrderSerializer, OrderItemSerializer, DrugUsageSerializer,
    NotificationsSerializer, PriceHistorySerializer
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
    filterset_fields = ['category', 'storage_unit', 'dispensing_unit']
    search_fields = ['name', 'generic_name', 'SKU', 'description']
    ordering_fields = ['name', 'current_stock', 'expiry_date', 'created_at']

    def get_queryset(self):
        return Drug.objects.select_related('category').prefetch_related('price_history')

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        drugs = Drug.objects.filter(
            Q(storage_count=0) & Q(loose_units=('reorder_level'))
        )
        
        serializer = self.get_serializer(drugs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        drugs = Drug.objects.filter(expiry_date__lt=now().date())
        serializer = self.get_serializer(drugs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        threshold = now().date() + timedelta(days=30)
        drugs = Drug.objects.filter(
            expiry_date__gt=now().date(),
            expiry_date__lte=threshold
        )
        serializer = self.get_serializer(drugs, many=True)
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
    ordering_fields = ['order_date', 'total_value']

    def get_queryset(self):
        return Order.objects.select_related('supplier').prefetch_related('items__drug')

    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_orders = self.get_queryset().filter(
            order_date__gte=now() - timedelta(days=30)
        ).order_by('-order_date')
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

class DrugUsageViewSet(viewsets.ModelViewSet):
    queryset = DrugUsage.objects.all()
    serializer_class = DrugUsageSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['usage_type', 'date', 'drug']
    ordering_fields = ['date', 'total_value']

    def get_queryset(self):
        return DrugUsage.objects.select_related('drug')

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usages = self.get_queryset().filter(date__range=[start_date, end_date])
        serializer = self.get_serializer(usages, many=True)
        return Response(serializer.data)

class NotificationsViewSet(viewsets.ModelViewSet):
    queryset = Notifications.objects.all()
    serializer_class = NotificationsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_read', 'notification_type']
    
    def get_queryset(self):
        queryset = Notifications.objects.select_related('drug')
        if self.action == 'list':
            return queryset.filter(is_read=False).order_by('-created_at')
        return queryset

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

class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'drug']
    ordering_fields = ['quantity', 'price_per_unit', 'total_value']

    def get_queryset(self):
        return OrderItem.objects.select_related('order', 'drug')

class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):  # ReadOnly because price history shouldn't be modified directly
    serializer_class = PriceHistorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['drug']
    ordering_fields = ['date_changed']

    def get_queryset(self):
        return PriceHistory.objects.select_related('drug').order_by('-date_changed')

    @action(detail=False, methods=['get'])
    def by_drug(self, request):
        drug_id = request.query_params.get('drug_id')
        if not drug_id:
            return Response(
                {"error": "drug_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        price_history = self.get_queryset().filter(drug_id=drug_id)
        serializer = self.get_serializer(price_history, many=True)
        return Response(serializer.data)
