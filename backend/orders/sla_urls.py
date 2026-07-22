from rest_framework.routers import SimpleRouter
from .sla_views import DeliveryPenaltyViewSet, SLAConfigViewSet

router = SimpleRouter()
router.register("penalties", DeliveryPenaltyViewSet, basename="penalty")
router.register("sla-config", SLAConfigViewSet, basename="sla-config")
urlpatterns = router.urls