from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import EditCategoryViewSet, EditPackageViewSet, EditStyleViewSet

router = DefaultRouter()
router.register("categories", EditCategoryViewSet, basename="edit-category")
router.register("styles", EditStyleViewSet, basename="edit-style")
router.register("packages", EditPackageViewSet, basename="edit-package")

urlpatterns = [
    path("", include(router.urls)),
]