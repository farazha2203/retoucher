from django.utils import timezone
from rest_framework import serializers

from accounts.serializers_editor import EditorProfileListSerializer
from catalog.serializers import EditPackageSerializer, EditStyleSerializer

from .models import ProjectRequest, ProjectRequestImage


class ProjectRequestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRequestImage
        fields = [
            "id",
            "image",
            "caption",
            "is_sample_image",
            "sort_order",
            "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at"]


class ProjectRequestListSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source="client.username", read_only=True)
    edit_style_title = serializers.CharField(source="edit_style.title", read_only=True)
    request_type_display = serializers.CharField(source="get_request_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProjectRequest
        fields = [
            "id",
            "client",
            "client_username",
            "request_type",
            "request_type_display",
            "status",
            "status_display",
            "title",
            "edit_style",
            "edit_style_title",
            "package",
            "target_editor",
            "budget_min",
            "budget_max",
            "preferred_deadline",
            "image_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "client",
            "client_username",
            "status",
            "image_count",
            "created_at",
            "updated_at",
        ]


class ProjectRequestDetailSerializer(ProjectRequestListSerializer):
    edit_style_detail = EditStyleSerializer(source="edit_style", read_only=True)
    package_detail = EditPackageSerializer(source="package", read_only=True)
    target_editor_detail = EditorProfileListSerializer(source="target_editor", read_only=True)
    images = ProjectRequestImageSerializer(many=True, read_only=True)

    class Meta(ProjectRequestListSerializer.Meta):
        fields = ProjectRequestListSerializer.Meta.fields + [
            "description",
            "client_note",
            "support_note",
            "submitted_at",
            "expires_at",
            "converted_order",
            "edit_style_detail",
            "package_detail",
            "target_editor_detail",
            "images",
        ]
        read_only_fields = ProjectRequestListSerializer.Meta.read_only_fields + [
            "support_note",
            "submitted_at",
            "expires_at",
            "converted_order",
        ]


class ProjectRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRequest
        fields = [
            "id",
            "request_type",
            "title",
            "description",
            "edit_style",
            "package",
            "target_editor",
            "budget_min",
            "budget_max",
            "preferred_deadline",
            "client_note",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        request_type = attrs.get("request_type", ProjectRequest.RequestType.MANAGED_ORDER)
        target_editor = attrs.get("target_editor")
        edit_style = attrs.get("edit_style")
        package = attrs.get("package")
        budget_min = attrs.get("budget_min", 0)
        budget_max = attrs.get("budget_max", 0)

        if package and edit_style and package.style_id != edit_style.id:
            raise serializers.ValidationError(
                {"package": "Selected package must belong to selected edit style."}
            )

        if request_type == ProjectRequest.RequestType.DIRECT_EDITOR:
            if not target_editor:
                raise serializers.ValidationError(
                    {"target_editor": "Direct editor request requires a target editor."}
                )
            if not target_editor.is_available or not target_editor.accepts_direct_requests:
                raise serializers.ValidationError(
                    {"target_editor": "Selected editor is not available for direct requests."}
                )
            if edit_style and not target_editor.skills.filter(id=edit_style.id).exists():
                raise serializers.ValidationError(
                    {"target_editor": "Selected editor does not support this edit style."}
                )

        if request_type == ProjectRequest.RequestType.PUBLIC_QUOTE:
            attrs["target_editor"] = None

        if request_type == ProjectRequest.RequestType.SAMPLE_CHALLENGE:
            attrs["target_editor"] = None

        if request_type == ProjectRequest.RequestType.MANAGED_ORDER:
            attrs["target_editor"] = None

        if budget_min and budget_max and budget_min > budget_max:
            raise serializers.ValidationError(
                {"budget_max": "Budget max must be greater than or equal to budget min."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        request_type = validated_data.get(
            "request_type",
            ProjectRequest.RequestType.MANAGED_ORDER,
        )

        status = ProjectRequest.Status.SUBMITTED
        if request_type == ProjectRequest.RequestType.PUBLIC_QUOTE:
            status = ProjectRequest.Status.OPEN_FOR_QUOTES
        elif request_type == ProjectRequest.RequestType.SAMPLE_CHALLENGE:
            status = ProjectRequest.Status.OPEN_FOR_SAMPLES
        elif request_type == ProjectRequest.RequestType.DIRECT_EDITOR:
            status = ProjectRequest.Status.WAITING_FOR_EDITOR
        elif request_type == ProjectRequest.RequestType.MANAGED_ORDER:
            status = ProjectRequest.Status.SUBMITTED

        return ProjectRequest.objects.create(
            client=request.user,
            status=status,
            submitted_at=timezone.now(),
            **validated_data,
        )


class ProjectRequestImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRequestImage
        fields = [
            "id",
            "image",
            "caption",
            "is_sample_image",
            "sort_order",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        project_request = self.context["project_request"]

        if project_request.status in [
            ProjectRequest.Status.CONVERTED_TO_ORDER,
            ProjectRequest.Status.CANCELLED,
            ProjectRequest.Status.EXPIRED,
        ]:
            raise serializers.ValidationError(
                "Cannot upload images to a closed project request."
            )

        return attrs

    def create(self, validated_data):
        project_request = self.context["project_request"]
        image = ProjectRequestImage.objects.create(
            project_request=project_request,
            **validated_data,
        )

        ProjectRequest.objects.filter(id=project_request.id).update(
            image_count=project_request.images.count()
        )

        return image