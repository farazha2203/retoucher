from django.contrib import admin

from .models import ProjectRequest, ProjectRequestImage


class ProjectRequestImageInline(admin.TabularInline):
    model = ProjectRequestImage
    extra = 0
    fields = (
        "image",
        "caption",
        "is_sample_image",
        "sort_order",
        "uploaded_at",
    )
    readonly_fields = ("uploaded_at",)


@admin.register(ProjectRequest)
class ProjectRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "client",
        "request_type",
        "status",
        "edit_style",
        "package",
        "target_editor",
        "budget_min",
        "budget_max",
        "image_count",
        "created_at",
    )
    list_filter = (
        "request_type",
        "status",
        "edit_style__category",
        "edit_style",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "client__username",
        "client__email",
        "target_editor__user__username",
        "target_editor__display_name",
    )
    readonly_fields = (
        "image_count",
        "submitted_at",
        "created_at",
        "updated_at",
    )
    inlines = [ProjectRequestImageInline]
    ordering = ("-created_at",)


@admin.register(ProjectRequestImage)
class ProjectRequestImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project_request",
        "caption",
        "is_sample_image",
        "sort_order",
        "uploaded_at",
    )
    list_filter = ("is_sample_image", "uploaded_at")
    search_fields = ("caption", "project_request__title", "project_request__client__username")