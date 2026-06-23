from rest_framework import decorators, permissions, response, status, viewsets
from .models import ProjectRequest
from django.db import models
from .permissions import IsProjectRequestOwnerOrStaff
from .serializers import (
    DirectEditorDeclineSerializer,
    DirectEditorProposalCreateSerializer,
    ProjectProposalSerializer,
    ProjectRequestCreateSerializer,
    ProjectRequestDetailSerializer,
    ProjectRequestImageCreateSerializer,
    ProjectRequestImageSerializer,
    ProjectRequestListSerializer,
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
                    models.Q(client=user) | models.Q(target_editor=editor_profile)
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
