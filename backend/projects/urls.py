from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectRequestViewSet

router = DefaultRouter()
router.register("requests", ProjectRequestViewSet, basename="project-request")

urlpatterns = [
    path("", include(router.urls)),
]