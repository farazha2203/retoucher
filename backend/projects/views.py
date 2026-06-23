from rest_framework import decorators, permissions, response, status, viewsets
from .models import ProjectRequest
from django.db import models
from .permissions import IsProjectRequestOwnerOrStaff
from .serializers import (
    ConvertProjectRequestToOrderSerializer,
    DirectEditorDeclineSerializer,
    DirectEditorProposalCreateSerializer,
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
