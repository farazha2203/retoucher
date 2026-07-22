from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalog.models import EditCategory, EditStyle

from .models import ProjectRequest, ProjectRequestActivity
from .workflow import transition_project_request


class ProjectWorkflowPhase1Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase1_project_client",
            password="test-pass",
            role="client",
        )
        category = EditCategory.objects.create(
            title="Phase 1 Category",
            slug="phase-1-category",
        )
        self.style = EditStyle.objects.create(
            category=category,
            title="Phase 1 Style",
            slug="phase-1-style",
        )
        self.project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Phase 1 request",
            edit_style=self.style,
            submitted_at=timezone.now(),
        )

    def test_valid_transition_updates_project(self):
        result = transition_project_request(
            project_request=self.project_request,
            to_status=ProjectRequest.Status.UNDER_REVIEW,
            actor=self.client_user,
        )

        self.assertEqual(result.status, ProjectRequest.Status.UNDER_REVIEW)
        self.project_request.refresh_from_db()
        self.assertEqual(
            self.project_request.status,
            ProjectRequest.Status.UNDER_REVIEW,
        )

    def test_transition_can_create_activity_with_status_metadata(self):
        transition_project_request(
            project_request=self.project_request,
            to_status=ProjectRequest.Status.EXPIRED,
            actor=None,
            action=ProjectRequestActivity.Action.EXPIRED,
            message="Expired by scheduler.",
            metadata={"source": "test"},
        )

        activity = ProjectRequestActivity.objects.get(
            project_request=self.project_request
        )
        self.assertEqual(activity.action, ProjectRequestActivity.Action.EXPIRED)
        self.assertEqual(activity.metadata["from_status"], ProjectRequest.Status.SUBMITTED)
        self.assertEqual(activity.metadata["to_status"], ProjectRequest.Status.EXPIRED)
        self.assertEqual(activity.metadata["source"], "test")

    def test_invalid_transition_does_not_create_activity(self):
        with self.assertRaises(ValidationError):
            transition_project_request(
                project_request=self.project_request,
                to_status=ProjectRequest.Status.CONVERTED_TO_ORDER,
                actor=self.client_user,
                action=ProjectRequestActivity.Action.CONVERTED_TO_ORDER,
            )

        self.project_request.refresh_from_db()
        self.assertEqual(self.project_request.status, ProjectRequest.Status.SUBMITTED)
        self.assertFalse(
            ProjectRequestActivity.objects.filter(
                project_request=self.project_request
            ).exists()
        )
