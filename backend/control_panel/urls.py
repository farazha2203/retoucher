from django.urls import path
from operations_hub import views as operations_views
from . import views

app_name = "control_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", views.PanelLogoutView.as_view(), name="logout"),

    path("orders/", views.orders_list, name="orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/actions/<slug:action_key>/", views.order_workflow_action, name="order_workflow_action"),
    path("projects/", views.projects_list, name="projects"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/actions/<slug:action_key>/", views.project_workflow_action, name="project_workflow_action"),
    path("users/", views.users_list, name="users"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("users/<int:pk>/toggle-verified/", views.user_toggle_verified, name="user_toggle_verified"),
    path("finance/", views.finance_dashboard, name="finance"),
    path("notifications/", views.notifications_center, name="notifications"),
    path("deadlines/", views.deadlines_center, name="deadlines"),
    path("backend/", views.backend_modules, name="backend_modules"),
    path("settings/", views.settings_home, name="settings"),

    path("messages/", operations_views.messages_home, name="messages"),
    path("messages/new/", operations_views.conversation_create, name="conversation_create"),
    path("messages/<int:pk>/", operations_views.conversation_detail, name="conversation_detail"),
    path("files/", operations_views.files_home, name="files"),
    path("files/<int:pk>/download/", operations_views.file_download, name="file_download"),
    path("files/<int:pk>/delete/", operations_views.file_delete, name="file_delete"),
    path("audit/", operations_views.audit_home, name="audit"),
]
