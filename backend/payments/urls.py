from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .refund_views import RefundEvidenceViewSet, RefundViewSet
from .settlement_views import SettlementAdminViewSet
from .views import WalletViewSet, WithdrawViewSet

router = DefaultRouter()
router.register("wallet", WalletViewSet, basename="wallet")
router.register("withdraw", WithdrawViewSet, basename="withdraw")
router.register("settlement", SettlementAdminViewSet, basename="settlement")
router.register("refunds", RefundViewSet, basename="refund")

refund_evidence = RefundEvidenceViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "refunds/<int:refund_pk>/evidence/",
        refund_evidence,
        name="refund-evidence-list",
    ),
]
