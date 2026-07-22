from rest_framework.routers import SimpleRouter
from .dispute_views import DisputeViewSet

router = SimpleRouter()
router.register("disputes", DisputeViewSet, basename="dispute")
urlpatterns = router.urls