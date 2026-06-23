from django.utils import timezone
from rest_framework import serializers

from accounts.serializers_editor import EditorProfileListSerializer
from catalog.serializers import EditPackageSerializer, EditStyleSerializer

from .models import ProjectProposal, ProjectRequest, ProjectRequestImage


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


class ProjectProposalSerializer(serializers.ModelSerializer):
    editor_username = serializers.CharField(
        source="editor.user.username", read_only=True
    )
    editor_display_name = serializers.CharField(
        source="editor.display_name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProjectProposal
        fields = [
            "id",
            "project_request",
            "editor",
            "editor_username",
            "editor_display_name",
            "status",
            "status_display",
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
            "client_note",
            "submitted_at",
            "updated_at",
            "accepted_at",
        ]
        read_only_fields = [
            "id",
            "project_request",
            "editor",
            "editor_username",
            "editor_display_name",
            "status",
            "status_display",
            "supervisor_score",
            "supervisor_note",
            "reviewed_by",
            "reviewed_at",
            "is_visible_to_client",
            "submitted_at",
            "updated_at",
            "accepted_at",
        ]


class ProjectRequestListSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source="client.username", read_only=True)
    edit_style_title = serializers.CharField(source="edit_style.title", read_only=True)
    request_type_display = serializers.CharField(
        source="get_request_type_display", read_only=True
    )
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
    target_editor_detail = EditorProfileListSerializer(
        source="target_editor", read_only=True
    )
    images = ProjectRequestImageSerializer(many=True, read_only=True)
    proposals = ProjectProposalSerializer(many=True, read_only=True)

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
            "proposals",
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
        request_type = attrs.get(
            "request_type", ProjectRequest.RequestType.MANAGED_ORDER
        )
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
            if (
                not target_editor.is_available
                or not target_editor.accepts_direct_requests
            ):
                raise serializers.ValidationError(
                    {
                        "target_editor": "Selected editor is not available for direct requests."
                    }
                )
            if (
                edit_style
                and not target_editor.skills.filter(id=edit_style.id).exists()
            ):
                raise serializers.ValidationError(
                    {
                        "target_editor": "Selected editor does not support this edit style."
                    }
                )

        if request_type == ProjectRequest.RequestType.PUBLIC_QUOTE:
            attrs["target_editor"] = None

        if request_type == ProjectRequest.RequestType.SAMPLE_CHALLENGE:
            attrs["target_editor"] = None

        if request_type == ProjectRequest.RequestType.MANAGED_ORDER:
            attrs["target_editor"] = None

        if budget_min and budget_max and budget_min > budget_max:
            raise serializers.ValidationError(
                {
                    "budget_max": "Budget max must be greater than or equal to budget min."
                }
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


class DirectEditorProposalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProposal
        fields = [
            "id",
            "proposed_price",
            "editor_fee",
            "estimated_delivery_hours",
            "editor_note",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        if project_request.request_type != ProjectRequest.RequestType.DIRECT_EDITOR:
            raise serializers.ValidationError(
                "This action is only available for direct editor requests."
            )

        if project_request.status != ProjectRequest.Status.WAITING_FOR_EDITOR:
            raise serializers.ValidationError(
                "This project request is not waiting for editor response."
            )

        if project_request.target_editor_id != editor_profile.id:
            raise serializers.ValidationError(
                "You are not the target editor for this request."
            )

        if ProjectProposal.objects.filter(
            project_request=project_request,
            editor=editor_profile,
        ).exists():
            raise serializers.ValidationError(
                "You have already responded to this project request."
            )

        proposed_price = attrs.get("proposed_price", 0)
        if proposed_price <= 0:
            raise serializers.ValidationError(
                {"proposed_price": "Proposed price must be greater than zero."}
            )

        estimated_delivery_hours = attrs.get("estimated_delivery_hours", 0)
        if estimated_delivery_hours <= 0:
            raise serializers.ValidationError(
                {
                    "estimated_delivery_hours": "Estimated delivery hours must be greater than zero."
                }
            )

        return attrs

    def create(self, validated_data):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            **validated_data,
        )

        project_request.status = ProjectRequest.Status.EDITOR_SELECTED
        project_request.save(update_fields=["status", "updated_at"])

        return proposal


class DirectEditorDeclineSerializer(serializers.Serializer):
    editor_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        if project_request.request_type != ProjectRequest.RequestType.DIRECT_EDITOR:
            raise serializers.ValidationError(
                "This action is only available for direct editor requests."
            )

        if project_request.status != ProjectRequest.Status.WAITING_FOR_EDITOR:
            raise serializers.ValidationError(
                "This project request is not waiting for editor response."
            )

        if project_request.target_editor_id != editor_profile.id:
            raise serializers.ValidationError(
                "You are not the target editor for this request."
            )

        return attrs

    def save(self, **kwargs):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]
        editor_note = self.validated_data.get("editor_note", "")

        proposal, _ = ProjectProposal.objects.update_or_create(
            project_request=project_request,
            editor=editor_profile,
            defaults={
                "status": ProjectProposal.Status.DECLINED_BY_EDITOR,
                "proposed_price": 0,
                "editor_fee": 0,
                "estimated_delivery_hours": 0,
                "editor_note": editor_note,
            },
        )

        project_request.status = ProjectRequest.Status.CANCELLED
        project_request.save(update_fields=["status", "updated_at"])

        return proposal


class PublicProposalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProposal
        fields = [
            "id",
            "proposed_price",
            "editor_fee",
            "estimated_delivery_hours",
            "editor_note",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        if project_request.request_type != ProjectRequest.RequestType.PUBLIC_QUOTE:
            raise serializers.ValidationError(
                "This action is only available for public quote requests."
            )

        if project_request.status != ProjectRequest.Status.OPEN_FOR_QUOTES:
            raise serializers.ValidationError(
                "This project request is not open for quotes."
            )

        if (
            not editor_profile.is_available
            or not editor_profile.accepts_public_requests
        ):
            raise serializers.ValidationError(
                "You are not available for public quote requests."
            )

        if not editor_profile.skills.filter(id=project_request.edit_style_id).exists():
            raise serializers.ValidationError("You do not support this edit style.")

        if ProjectProposal.objects.filter(
            project_request=project_request,
            editor=editor_profile,
        ).exists():
            raise serializers.ValidationError(
                "You have already submitted a proposal for this project request."
            )

        proposed_price = attrs.get("proposed_price", 0)
        if proposed_price <= 0:
            raise serializers.ValidationError(
                {"proposed_price": "Proposed price must be greater than zero."}
            )

        estimated_delivery_hours = attrs.get("estimated_delivery_hours", 0)
        if estimated_delivery_hours <= 0:
            raise serializers.ValidationError(
                {
                    "estimated_delivery_hours": "Estimated delivery hours must be greater than zero."
                }
            )

        return attrs

    def create(self, validated_data):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        return ProjectProposal.objects.create(
            project_request=project_request,
            editor=editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            **validated_data,
        )


class SelectProjectProposalSerializer(serializers.Serializer):
    client_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        project_request = self.context["project_request"]
        proposal = self.context["proposal"]
        request = self.context["request"]

        if project_request.client_id != request.user.id and not request.user.is_staff:
            raise serializers.ValidationError(
                "Only the client or staff can select a proposal."
            )

        if project_request.status not in [
            ProjectRequest.Status.OPEN_FOR_QUOTES,
            ProjectRequest.Status.OPEN_FOR_SAMPLES,
            ProjectRequest.Status.EDITOR_SELECTED,
        ]:
            raise serializers.ValidationError(
                "This project request is not open for proposal selection."
            )

        if proposal.project_request_id != project_request.id:
            raise serializers.ValidationError(
                "Proposal does not belong to this project request."
            )

        if project_request.request_type == ProjectRequest.RequestType.SAMPLE_CHALLENGE:
            if proposal.status != ProjectProposal.Status.APPROVED:
                raise serializers.ValidationError(
                    "Only approved sample proposals can be selected."
                )
            if not proposal.is_visible_to_client:
                raise serializers.ValidationError(
                    "This sample proposal is not visible to client."
                )
        else:
            if proposal.status != ProjectProposal.Status.SUBMITTED:
                raise serializers.ValidationError(
                    "Only submitted proposals can be selected."
                )

        return attrs

    def save(self, **kwargs):
        project_request = self.context["project_request"]
        proposal = self.context["proposal"]
        client_note = self.validated_data.get("client_note", "")

        ProjectProposal.objects.filter(
            project_request=project_request,
            status=ProjectProposal.Status.SUBMITTED,
        ).exclude(id=proposal.id).update(
            status=ProjectProposal.Status.REJECTED_BY_CLIENT
        )

        proposal.status = ProjectProposal.Status.ACCEPTED_BY_CLIENT
        proposal.client_note = client_note
        proposal.accepted_at = timezone.now()
        proposal.save(
            update_fields=["status", "client_note", "accepted_at", "updated_at"]
        )

        project_request.target_editor = proposal.editor
        project_request.status = ProjectRequest.Status.EDITOR_SELECTED
        project_request.save(update_fields=["target_editor", "status", "updated_at"])

        return proposal


class SampleProposalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProposal
        fields = [
            "id",
            "proposed_price",
            "editor_fee",
            "estimated_delivery_hours",
            "editor_note",
            "sample_file",
            "sample_note",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        if project_request.request_type != ProjectRequest.RequestType.SAMPLE_CHALLENGE:
            raise serializers.ValidationError(
                "This action is only available for sample challenge requests."
            )

        if project_request.status != ProjectRequest.Status.OPEN_FOR_SAMPLES:
            raise serializers.ValidationError(
                "This project request is not open for sample submissions."
            )

        if (
            not editor_profile.is_available
            or not editor_profile.accepts_sample_challenges
        ):
            raise serializers.ValidationError(
                "You are not available for sample challenge requests."
            )

        if not editor_profile.skills.filter(id=project_request.edit_style_id).exists():
            raise serializers.ValidationError("You do not support this edit style.")

        if ProjectProposal.objects.filter(
            project_request=project_request,
            editor=editor_profile,
        ).exists():
            raise serializers.ValidationError(
                "You have already submitted a sample proposal for this project request."
            )

        proposed_price = attrs.get("proposed_price", 0)
        if proposed_price <= 0:
            raise serializers.ValidationError(
                {"proposed_price": "Proposed price must be greater than zero."}
            )

        estimated_delivery_hours = attrs.get("estimated_delivery_hours", 0)
        if estimated_delivery_hours <= 0:
            raise serializers.ValidationError(
                {
                    "estimated_delivery_hours": "Estimated delivery hours must be greater than zero."
                }
            )

        sample_file = attrs.get("sample_file")
        if not sample_file:
            raise serializers.ValidationError(
                {"sample_file": "Sample challenge proposal requires a sample file."}
            )

        return attrs

    def create(self, validated_data):
        project_request = self.context["project_request"]
        editor_profile = self.context["editor_profile"]

        return ProjectProposal.objects.create(
            project_request=project_request,
            editor=editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            is_visible_to_client=False,
            **validated_data,
        )


class ReviewSampleProposalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    supervisor_score = serializers.IntegerField(
        required=False, min_value=1, max_value=10
    )
    supervisor_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        proposal = self.context["proposal"]

        if (
            proposal.project_request.request_type
            != ProjectRequest.RequestType.SAMPLE_CHALLENGE
        ):
            raise serializers.ValidationError(
                "This proposal does not belong to a sample challenge request."
            )

        if proposal.status not in [
            ProjectProposal.Status.UNDER_REVIEW,
            ProjectProposal.Status.SUBMITTED,
            ProjectProposal.Status.APPROVED,
            ProjectProposal.Status.REJECTED_BY_SUPERVISOR,
        ]:
            raise serializers.ValidationError("This proposal cannot be reviewed.")

        action = attrs.get("action")
        supervisor_score = attrs.get("supervisor_score")

        if action == "approve" and supervisor_score is None:
            raise serializers.ValidationError(
                {"supervisor_score": "Supervisor score is required when approving."}
            )

        return attrs

    def save(self, **kwargs):
        request = self.context["request"]
        proposal = self.context["proposal"]

        action = self.validated_data["action"]
        supervisor_score = self.validated_data.get("supervisor_score")
        supervisor_note = self.validated_data.get("supervisor_note", "")

        if action == "approve":
            proposal.status = ProjectProposal.Status.APPROVED
            proposal.is_visible_to_client = True
            proposal.supervisor_score = supervisor_score
        else:
            proposal.status = ProjectProposal.Status.REJECTED_BY_SUPERVISOR
            proposal.is_visible_to_client = False
            proposal.supervisor_score = supervisor_score

        proposal.supervisor_note = supervisor_note
        proposal.reviewed_by = request.user
        proposal.reviewed_at = timezone.now()
        proposal.save(
            update_fields=[
                "status",
                "is_visible_to_client",
                "supervisor_score",
                "supervisor_note",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        return proposal
