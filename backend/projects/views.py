from rest_framework import decorators, permissions, response, status, viewsets
from .models import ProjectProposal, ProjectRequest
from django.db import models
from .permissions import IsProjectRequestOwnerOrStaff, IsProjectRequestParticipantOrStaff
from .serializers import (
    ConvertProjectRequestToOrderSerializer,
    DirectEditorDeclineSerializer,
    DirectEditorProposalCreateSerializer,
    ManagedAssignProjectRequestSerializer,
    ProjectProposalSerializer,
    ProjectRequestCreateSerializer,
    ProjectRequestDetailSerializer,
    ProjectRequestImageCreateSerializer,
    ProjectRequestImageSerializer,
    ProjectRequestListSerializer,
    PublicProposalCreateSerializer,
    ReviewSampleProposalSerializer,
    SampleProposalCreateSerializer,
    SelectProjectProposalSerializer,
)


class ProjectRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsProjectRequestOwnerOrStaff]
    def get_permissions(self):
        if self.action == "retrieve":
            return [
                permissions.IsAuthenticated(),
                IsProjectRequestParticipantOrStaff(),
            ]

        return super().get_permissions()

    def get_editor_profile(self):
        return getattr(self.request.user, "editor_profile", None)

    def get_queryset(self):
        queryset = (
            ProjectRequest.objects.select_related(
                "client",
                "edit_style",
                "edit_style__category",
                "package",
                "target_editor",
                "target_editor__user",
                "converted_order",
            )
            .prefetch_related(
                "images",
                "edit_style__packages",
                "target_editor__skills",
                "target_editor__skills__category",
                "target_editor__skills__packages",
            )
            .order_by("-created_at")
        )

        user = self.request.user

        if not user.is_staff:
            editor_profile = getattr(user, "editor_profile", None)

            if editor_profile:
                queryset = queryset.filter(
                    models.Q(client=user)
                    | models.Q(target_editor=editor_profile)
                    | models.Q(
                        request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
                        status=ProjectRequest.Status.OPEN_FOR_QUOTES,
                        edit_style__in=editor_profile.skills.all(),
                    )
                    | models.Q(
                        request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
                        status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
                        edit_style__in=editor_profile.skills.all(),
                    )
                )
            else:
                queryset = queryset.filter(client=user)

        request_type = self.request.query_params.get("request_type")
        if request_type:
            queryset = queryset.filter(request_type=request_type)

        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        edit_style = self.request.query_params.get("edit_style")
        if edit_style:
            queryset = queryset.filter(edit_style__slug=edit_style)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectRequestCreateSerializer
        if self.action == "upload_image":
            return ProjectRequestImageCreateSerializer
        if self.action == "direct_proposal":
            return DirectEditorProposalCreateSerializer
        if self.action == "direct_decline":
            return DirectEditorDeclineSerializer
        if self.action == "retrieve":
            return ProjectRequestDetailSerializer
        if self.action == "public_proposal":
            return PublicProposalCreateSerializer
        if self.action == "select_proposal":
            return SelectProjectProposalSerializer
        if self.action == "sample_proposal":
            return SampleProposalCreateSerializer
        if self.action == "review_sample_proposal":
            return ReviewSampleProposalSerializer
        if self.action == "convert_to_order":
            return ConvertProjectRequestToOrderSerializer
        if self.action == "managed_assign":
            return ManagedAssignProjectRequestSerializer
        return ProjectRequestListSerializer

    def perform_create(self, serializer):
        serializer.save()

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="images",
        permission_classes=[permissions.IsAuthenticated, IsProjectRequestOwnerOrStaff],
    )
    def upload_image(self, request, pk=None):
        project_request = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
            },
        )
        serializer.is_valid(raise_exception=True)
        image = serializer.save()

        output_serializer = ProjectRequestImageSerializer(
            image,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="direct-proposal",
        permission_classes=[permissions.IsAuthenticated],
    )
    def direct_proposal(self, request, pk=None):
        project_request = self.get_object()
        editor_profile = self.get_editor_profile()

        if editor_profile is None:
            return response.Response(
                {"detail": "Only editors can respond to direct requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
                "editor_profile": editor_profile,
            },
        )
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="direct-decline",
        permission_classes=[permissions.IsAuthenticated],
    )
    def direct_decline(self, request, pk=None):
        project_request = self.get_object()
        editor_profile = self.get_editor_profile()

        if editor_profile is None:
            return response.Response(
                {"detail": "Only editors can decline direct requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
                "editor_profile": editor_profile,
            },
        )
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_200_OK,
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="public-proposal",
        permission_classes=[permissions.IsAuthenticated],
    )
    def public_proposal(self, request, pk=None):
        project_request = self.get_object()
        editor_profile = self.get_editor_profile()

        if editor_profile is None:
            return response.Response(
                {"detail": "Only editors can submit public proposals."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
                "editor_profile": editor_profile,
            },
        )
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path=r"proposals/(?P<proposal_id>[^/.]+)/select",
        permission_classes=[permissions.IsAuthenticated],
    )
    def select_proposal(self, request, pk=None, proposal_id=None):
        project_request = self.get_object()

        try:
            proposal = project_request.proposals.get(id=proposal_id)
        except Exception:
            return response.Response(
                {"detail": "Proposal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
                "proposal": proposal,
            },
        )
        serializer.is_valid(raise_exception=True)
        selected_proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            selected_proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_200_OK,
        )
    
    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="sample-proposal",
        permission_classes=[permissions.IsAuthenticated],
    )
    def sample_proposal(self, request, pk=None):
        project_request = self.get_object()
        editor_profile = self.get_editor_profile()

        if editor_profile is None:
            return response.Response(
                {"detail": "Only editors can submit sample proposals."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
                "editor_profile": editor_profile,
            },
        )
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path=r"proposals/(?P<proposal_id>[^/.]+)/review-sample",
        permission_classes=[permissions.IsAdminUser],
    )
    def review_sample_proposal(self, request, pk=None, proposal_id=None):
        project_request = self.get_object()

        try:
            proposal = project_request.proposals.get(id=proposal_id)
        except Exception:
            return response.Response(
                {"detail": "Proposal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
                "proposal": proposal,
            },
        )
        serializer.is_valid(raise_exception=True)
        reviewed_proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            reviewed_proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_200_OK,
        )
    
    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="convert-to-order",
        permission_classes=[permissions.IsAuthenticated],
    )
    def convert_to_order(self, request, pk=None):
        project_request = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
            },
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        return response.Response(
            {
                "id": order.id,
                "order_id": order.id,
                "project_request_id": project_request.id,
                "status": order.status,
                "title": order.title,
                "client": order.client_id,
                "editor": order.editor_id,
                "deadline": order.deadline,
            },
            status=status.HTTP_201_CREATED,
        )
    
    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="dashboard-summary",
        permission_classes=[permissions.IsAdminUser],
    )
    def dashboard_summary(self, request):
        project_requests = ProjectRequest.objects.all()
        proposals = ProjectProposal.objects.all()

        requests_by_status = {
            item["status"]: item["count"]
            for item in project_requests.values("status")
            .annotate(count=models.Count("id"))
            .order_by("status")
        }

        requests_by_type = {
            item["request_type"]: item["count"]
            for item in project_requests.values("request_type")
            .annotate(count=models.Count("id"))
            .order_by("request_type")
        }

        proposals_by_status = {
            item["status"]: item["count"]
            for item in proposals.values("status")
            .annotate(count=models.Count("id"))
            .order_by("status")
        }

        latest_requests = [
            {
                "id": item.id,
                "title": item.title,
                "request_type": item.request_type,
                "status": item.status,
                "client": item.client_id,
                "edit_style": item.edit_style_id,
                "created_at": item.created_at,
            }
            for item in project_requests.select_related("client", "edit_style").order_by("-created_at")[:10]
        ]

        return response.Response(
            {
                "total_requests": project_requests.count(),
                "total_proposals": proposals.count(),
                "requests_by_status": requests_by_status,
                "requests_by_type": requests_by_type,
                "proposals_by_status": proposals_by_status,
                "latest_requests": latest_requests,
            },
            status=status.HTTP_200_OK,
        )
    
    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="managed-assign",
        permission_classes=[permissions.IsAdminUser],
    )
    def managed_assign(self, request, pk=None):
        project_request = self.get_object()

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "project_request": project_request,
            },
        )
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save()

        output_serializer = ProjectProposalSerializer(
            proposal,
            context={"request": request},
        )

        return response.Response(
            output_serializer.data,
            status=status.HTTP_200_OK,
        )
