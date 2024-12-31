from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'orders', views.OrdersViewSet)
router.register(r'usages', views.UsageViewSet)
router.register(r'notifications', views.NotificationViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]

# This will generate the following URL patterns:
# API endpoints:
# /categories/
# /categories/{id}/
# /categories/{id}/products/
# /products/
# /products/{id}/
# /products/low_stock/
# /products/out_of_stock/
# /suppliers/
# /suppliers/{id}/
# /suppliers/{id}/orders/
# /orders/
# /orders/{id}/
# /orders/recent/
# /orders/{id}/update_status/
# /usages/
# /usages/{id}/
# /usages/by_date_range/
# /notifications/
# /notifications/{id}/
# /notifications/mark_all_as_read/
# /notifications/{id}/mark_as_read/ 