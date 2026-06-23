from django.contrib import admin
from .models import ProjectProposal, ProjectRequest, ProjectRequestImage


class ProjectProposalInline(admin.TabularInline):
    model = ProjectProposal
    extra = 0
    fields = (
        "editor",
        "status",
        "proposed_price",
        "editor_fee",
        "estimated_delivery_hours",
        "editor_note",
        "submitted_at",
        "accepted_at",
    )
    readonly_fields = ("submitted_at", "accepted_at")


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
    inlines = [ProjectRequestImageInline, ProjectProposalInline]
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

@admin.register(ProjectProposal)
class ProjectProposalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project_request",
        "editor",
        "status",
        "proposed_price",
        "editor_fee",
        "estimated_delivery_hours",
        "submitted_at",
        "accepted_at",
    )
    list_filter = (
        "status",
        "project_request__request_type",
        "submitted_at",
    )
    search_fields = (
        "project_request__title",
        "editor__user__username",
        "editor__display_name",
        "editor_note",
    )
    ordering = ("-submitted_at",)