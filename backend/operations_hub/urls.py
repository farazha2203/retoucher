from django.urls import path

from . import views

app_name = "operations_hub"

urlpatterns = [
    path("messages/", views.messages_home, name="messages"),
    path("messages/new/", views.conversation_create, name="conversation_create"),
    path("messages/<int:pk>/", views.conversation_detail, name="conversation_detail"),
    path("files/", views.files_home, name="files"),
    path("files/<int:pk>/download/", views.file_download, name="file_download"),
    path("files/<int:pk>/delete/", views.file_delete, name="file_delete"),
    path("audit/", views.audit_home, name="audit"),
]
