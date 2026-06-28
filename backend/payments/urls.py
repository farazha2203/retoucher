from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WalletViewSet, WithdrawViewSet

router = DefaultRouter()
router.register("wallet", WalletViewSet, basename="wallet")
router.register("withdraw", WithdrawViewSet, basename="withdraw")

urlpatterns = [
    path("", include(router.urls)),
]
