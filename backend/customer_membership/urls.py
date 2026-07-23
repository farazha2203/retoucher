from django.urls import path
from .api_views import PurchaseMembershipView
from .dashboard_api import EditorLeaderboardView, StudioDirectoryView
from .views import CustomerProfileMeView, CustomerTierListView

app_name = "customer_membership"
urlpatterns = [
    path("leaderboard/editors/", EditorLeaderboardView.as_view(), name="editor-leaderboard"),
    path("studios/", StudioDirectoryView.as_view(), name="studio-directory"),
    path("membership/purchase/", PurchaseMembershipView.as_view(), name="membership-purchase"),
    path("profile/me/", CustomerProfileMeView.as_view(), name="profile-me"),
    path("tiers/", CustomerTierListView.as_view(), name="tiers"),
]
