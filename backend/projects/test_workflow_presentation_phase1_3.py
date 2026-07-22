from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import EditCategory, EditStyle

from .models import ProjectRequest, ProjectRequestActivity
from .workflow_presentation import build_project_timeline, get_project_workflow_summary


class ProjectWorkflowPresentationPhase13Tests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="project-client-p13", password="pass")
        category = EditCategory.objects.create(title="P13", slug="p13")
        style = EditStyle.objects.create(category=category, title="P13 Style", slug="p13-style")
        self.project = ProjectRequest.objects.create(
            client=self.user,
            title="Phase 1.3 project",
            edit_style=style,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            submitted_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=8),
        )

    def test_summary_contains_request_type_and_progress(self):
        data = get_project_workflow_summary(self.project)
        self.assertEqual(data["request_type"], ProjectRequest.RequestType.PUBLIC_QUOTE)
        self.assertEqual(data["stage"]["key"], "quotes")
        self.assertEqual(data["progress_percent"], 30)
        self.assertFalse(data["terminal"])

    def test_timeline_uses_stable_event_shape(self):
        activity = ProjectRequestActivity.objects.create(
            project_request=self.project,
            actor=self.user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Created",
            metadata={"from_status": "draft", "to_status": "open_for_quotes"},
        )
        events = build_project_timeline(self.project)
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["event_id"], f"project-activity-{activity.pk}")
        self.assertEqual(event["entity_type"], "project_request")
        self.assertEqual(event["from_status"], "draft")
        self.assertEqual(event["to_status"], "open_for_quotes")
