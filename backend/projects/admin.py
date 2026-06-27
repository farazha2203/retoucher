from django.contrib import admin
from .models import ProjectProposal, ProjectRequest, ProjectRequestActivity, ProjectRequestImage


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
        "sample_file",
        "sample_note",
        "supervisor_score",
        "supervisor_note",
        "reviewed_by",
        "reviewed_at",
        "is_visible_to_client",
        "submitted_at",
        "accepted_at",
    )
    readonly_fields = ("submitted_at", "accepted_at", "reviewed_at")


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

class ProjectRequestActivityInline(admin.TabularInline):
    model = ProjectRequestActivity
    extra = 0
    fields = (
        "actor",
        "action",
        "message",
        "metadata",
        "created_at",
    )
    readonly_fields = (
        "actor",
        "action",
        "message",
        "metadata",
        "created_at",
    )
    can_delete = False

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
    inlines = [ProjectRequestImageInline, ProjectProposalInline, ProjectRequestActivityInline]
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
        "supervisor_score",
        "is_visible_to_client",
        "submitted_at",
        "reviewed_at",
        "accepted_at",
    )
    list_filter = (
        "status",
        "is_visible_to_client",
        "project_request__request_type",
        "supervisor_score",
        "submitted_at",
    )
    search_fields = (
        "project_request__title",
        "editor__user__username",
        "editor__display_name",
        "editor_note",
        "sample_note",
        "supervisor_note",
    )
    readonly_fields = (
        "submitted_at",
        "updated_at",
        "reviewed_at",
        "accepted_at",
    )
    ordering = ("-submitted_at",)

@admin.register(ProjectRequestActivity)
class ProjectRequestActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project_request",
        "actor",
        "action",
        "created_at",
    )
    list_filter = (
        "action",
        "created_at",
    )
    search_fields = (
        "project_request__title",
        "actor__username",
        "actor__email",
        "message",
    )
    readonly_fields = (
        "project_request",
        "actor",
        "action",
        "message",
        "metadata",
        "created_at",
    )
    ordering = ("-created_at",)