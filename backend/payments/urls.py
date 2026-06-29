from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .settlement_views import SettlementAdminViewSet
from .views import WalletViewSet, WithdrawViewSet

router = DefaultRouter()
router.register("wallet", WalletViewSet, basename="wallet")
router.register("withdraw", WithdrawViewSet, basename="withdraw")
router.register("settlement", SettlementAdminViewSet, basename="settlement")

urlpatterns = [
    path("", include(router.urls)),
]