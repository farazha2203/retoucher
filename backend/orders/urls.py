from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import OrderViewSet
from .sla_views import DeliveryPenaltyViewSet, SLAConfigViewSet

order_router = SimpleRouter()
order_router.register("orders", OrderViewSet, basename="orders")  # ✅ prefix "orders" اضافه شد

extra_router = SimpleRouter()
extra_router.register("penalties", DeliveryPenaltyViewSet, basename="penalty")
extra_router.register("sla-config", SLAConfigViewSet, basename="sla-config")

urlpatterns = [
    path("", include(order_router.urls)),
    path("", include(extra_router.urls)),
]