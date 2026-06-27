from django.utils import timezone
from rest_framework import serializers
from datetime import timedelta

from django.db import models, transaction

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
    target_editor_detail = EditorProfileListSerializer(source="target_editor", read_only=True)
    images = ProjectRequestImageSerializer(many=True, read_only=True)
    proposals = serializers.SerializerMethodField()

    class Meta:
        model = ProjectRequest
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

    def get_proposals(self, obj):
        request = self.context.get("request")
        proposals = obj.proposals.select_related("editor", "editor__user").order_by("-submitted_at")

        if request is None or not request.user.is_authenticated:
            proposals = proposals.none()
        elif request.user.is_staff:
            pass
        elif obj.client_id == request.user.id:
            proposals = proposals.filter(
                models.Q(is_visible_to_client=True)
                | models.Q(status=ProjectProposal.Status.ACCEPTED_BY_CLIENT)
                | models.Q(
                    project_request__request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
                    status=ProjectProposal.Status.SUBMITTED,
                )
                | models.Q(
                    project_request__request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
                    status=ProjectProposal.Status.APPROVED,
                )
            )
        else:
            editor_profile = getattr(request.user, "editor_profile", None)

            if editor_profile:
                proposals = proposals.filter(editor=editor_profile)
            else:
                proposals = proposals.none()

        serializer = ProjectProposalSerializer(
            proposals,
            many=True,
            context=self.context,
        )
        return serializer.data


class ProjectRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRequest
        fields = [
            "id",
            "request_type",
            "status",
            "title",
            "description",
            "edit_style",
            "package",
            "target_editor",
            "budget_min",
            "budget_max",
            "preferred_deadline",
            "client_note",
            "submitted_at",
        ]
        read_only_fields = ["id", "status", "submitted_at"]

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


class ConvertProjectRequestToOrderSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        project_request = self.context["project_request"]
        request = self.context["request"]

        if project_request.client_id != request.user.id and not request.user.is_staff:
            raise serializers.ValidationError(
                "Only the client or staff can convert this project request to an order."
            )

        if project_request.status != ProjectRequest.Status.EDITOR_SELECTED:
            raise serializers.ValidationError(
                "Only project requests with selected editor can be converted to order."
            )

        if project_request.target_editor_id is None:
            raise serializers.ValidationError(
                "Project request must have a selected editor before conversion."
            )

        if project_request.converted_order_id is not None:
            raise serializers.ValidationError(
                "This project request has already been converted to an order."
            )

        accepted_proposal = project_request.proposals.filter(
            status=ProjectProposal.Status.ACCEPTED_BY_CLIENT
        ).first()

        submitted_proposal = project_request.proposals.filter(
            editor=project_request.target_editor,
            status=ProjectProposal.Status.SUBMITTED,
        ).first()

        # Direct editor workflow currently creates a submitted proposal and marks request editor_selected.
        proposal = accepted_proposal or submitted_proposal

        if (
            project_request.request_type
            in [
                ProjectRequest.RequestType.PUBLIC_QUOTE,
                ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            ]
            and accepted_proposal is None
        ):
            raise serializers.ValidationError(
                "Public quote and sample challenge requests require an accepted proposal."
            )

        attrs["proposal"] = proposal

        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        from orders.models import (
            Order,
            OrderActivityLog,
            OrderImage,
            OrderStatusHistory,
        )

        project_request = self.context["project_request"]
        request = self.context["request"]
        proposal = self.validated_data.get("proposal")
        note = self.validated_data.get("note", "")

        deadline = None
        if proposal and proposal.estimated_delivery_hours:
            deadline = timezone.now() + timedelta(
                hours=proposal.estimated_delivery_hours
            )
        elif project_request.preferred_deadline:
            deadline = project_request.preferred_deadline

        description_parts = []

        if project_request.description:
            description_parts.append(project_request.description)

        if project_request.client_note:
            description_parts.append(f"Client note: {project_request.client_note}")

        if proposal and proposal.editor_note:
            description_parts.append(f"Editor proposal note: {proposal.editor_note}")

        if note:
            description_parts.append(f"Conversion note: {note}")

        order = Order.objects.create(
            client=project_request.client,
            editor=project_request.target_editor.user,
            title=project_request.title,
            description="\n\n".join(description_parts),
            status=Order.Status.ASSIGNED,
            deadline=deadline,
        )

        for project_image in project_request.images.all():
            OrderImage.objects.create(
                order=order,
                image=project_image.image,
                note=project_image.caption,
            )

        OrderStatusHistory.objects.create(
            order=order,
            changed_by=request.user,
            from_status="",
            to_status=Order.Status.ASSIGNED,
            note="Order created from project request.",
        )

        OrderActivityLog.objects.create(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.EDITOR_ASSIGNED,
            message="Project request converted to order and editor assigned.",
            metadata={
                "project_request_id": project_request.id,
                "request_type": project_request.request_type,
                "proposal_id": proposal.id if proposal else None,
                "proposed_price": proposal.proposed_price if proposal else None,
                "editor_fee": proposal.editor_fee if proposal else None,
                "estimated_delivery_hours": (
                    proposal.estimated_delivery_hours if proposal else None
                ),
                "edit_style_id": project_request.edit_style_id,
                "package_id": project_request.package_id,
            },
        )

        project_request.status = ProjectRequest.Status.CONVERTED_TO_ORDER
        project_request.converted_order = order
        project_request.save(
            update_fields=[
                "status",
                "converted_order",
                "updated_at",
            ]
        )

        return order


class ManagedAssignProjectRequestSerializer(serializers.Serializer):
    editor = serializers.IntegerField()
    proposed_price = serializers.IntegerField(min_value=1)
    editor_fee = serializers.IntegerField(min_value=0, required=False, default=0)
    estimated_delivery_hours = serializers.IntegerField(min_value=1)
    editor_note = serializers.CharField(required=False, allow_blank=True)
    support_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        from accounts.models import EditorProfile

        project_request = self.context["project_request"]

        if project_request.request_type != ProjectRequest.RequestType.MANAGED_ORDER:
            raise serializers.ValidationError(
                "This action is only available for managed order requests."
            )

        if project_request.status not in [
            ProjectRequest.Status.SUBMITTED,
            ProjectRequest.Status.UNDER_REVIEW,
            ProjectRequest.Status.EDITOR_SELECTED,
        ]:
            raise serializers.ValidationError(
                "This managed order request cannot be assigned in its current status."
            )

        if project_request.converted_order_id is not None:
            raise serializers.ValidationError(
                "This project request has already been converted to an order."
            )

        editor_id = attrs.get("editor")

        try:
            editor_profile = EditorProfile.objects.get(id=editor_id)
        except EditorProfile.DoesNotExist:
            raise serializers.ValidationError({"editor": "Editor profile not found."})

        if not editor_profile.is_available:
            raise serializers.ValidationError(
                {"editor": "Selected editor is not available."}
            )

        if not editor_profile.skills.filter(id=project_request.edit_style_id).exists():
            raise serializers.ValidationError(
                {"editor": "Selected editor does not support this edit style."}
            )

        attrs["editor_profile"] = editor_profile

        return attrs

    def save(self, **kwargs):
        project_request = self.context["project_request"]
        request = self.context["request"]

        editor_profile = self.validated_data["editor_profile"]
        proposed_price = self.validated_data["proposed_price"]
        editor_fee = self.validated_data.get("editor_fee", 0)
        estimated_delivery_hours = self.validated_data["estimated_delivery_hours"]
        editor_note = self.validated_data.get("editor_note", "")
        support_note = self.validated_data.get("support_note", "")

        # Reject previous submitted/accepted proposals for this managed request.
        ProjectProposal.objects.filter(
            project_request=project_request,
        ).exclude(
            editor=editor_profile,
        ).update(
            status=ProjectProposal.Status.REJECTED_BY_CLIENT,
        )

        proposal, _ = ProjectProposal.objects.update_or_create(
            project_request=project_request,
            editor=editor_profile,
            defaults={
                "status": ProjectProposal.Status.ACCEPTED_BY_CLIENT,
                "proposed_price": proposed_price,
                "editor_fee": editor_fee,
                "estimated_delivery_hours": estimated_delivery_hours,
                "editor_note": editor_note,
                "client_note": "Assigned by support/admin.",
                "accepted_at": timezone.now(),
                "is_visible_to_client": True,
            },
        )

        project_request.target_editor = editor_profile
        project_request.status = ProjectRequest.Status.EDITOR_SELECTED

        if support_note:
            project_request.support_note = support_note

        project_request.save(
            update_fields=[
                "target_editor",
                "status",
                "support_note",
                "updated_at",
            ]
        )

        return proposal
