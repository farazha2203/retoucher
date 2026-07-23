from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MeView, RegisterView
from .social_auth_views import SocialAuthExchangeView, frontend_auth_bridge
from .views_editor import EditorProfileViewSet
from .portfolio_social import (
    PortfolioCommentModerationViewSet,
    PortfolioSocialViewSet,
)

app_name = "accounts"

router = DefaultRouter()
router.register("editors", EditorProfileViewSet, basename="editor-profile")
router.register("portfolio", PortfolioSocialViewSet, basename="portfolio-social")
router.register("portfolio-comments", PortfolioCommentModerationViewSet, basename="portfolio-comment-moderation")


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("social/exchange/", SocialAuthExchangeView.as_view(), name="social-auth-exchange"),
    path("frontend-bridge/", frontend_auth_bridge, name="frontend-auth-bridge"),
    path("", include(router.urls)),
]