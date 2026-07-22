from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MeView, RegisterView
from .views_editor import EditorProfileViewSet

router = DefaultRouter()
router.register("editors", EditorProfileViewSet, basename="editor-profile")


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]