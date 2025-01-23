from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'drug-categories', views.DrugCategoryViewSet)
router.register(r'drugs', views.DrugViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'order-items', views.OrderItemViewSet, basename='order-item')
router.register(r'drug-usages', views.DrugUsageViewSet)
router.register(r'notifications', views.NotificationsViewSet)
router.register(r'price-history', views.PriceHistoryViewSet, basename='price-history')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]

# This will generate the following URL patterns:
# API endpoints:
# /drug-categories/
# /drug-categories/{id}/
# /drug-categories/{id}/drugs/
# /drugs/
# /drugs/{id}/
# /drugs/low_stock/
# /drugs/expired/
# /drugs/expiring_soon/
# /suppliers/
# /suppliers/{id}/
# /suppliers/{id}/orders/
# /orders/
# /orders/{id}/
# /orders/recent/
# /orders/{id}/update_status/
# /order-items/
# /order-items/{id}/
# /drug-usages/
# /drug-usages/{id}/
# /drug-usages/by_date_range/
# /notifications/
# /notifications/{id}/
# /notifications/mark_all_as_read/
# /notifications/{id}/mark_as_read/
# /price-history/
# /price-history/{id}/
# /price-history/by_drug/ 