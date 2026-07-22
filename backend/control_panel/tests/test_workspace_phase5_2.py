from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import EditCategory, EditStyle
from orders.models import Order
from projects.models import ProjectRequest


class PanelWorkspacePhase52Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase52_client",
            password="test-pass-123",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="phase52_editor",
            password="test-pass-123",
            role="editor",
        )
        self.staff_user = User.objects.create_user(
            username="phase52_admin",
            password="test-pass-123",
            role="admin",
            is_staff=True,
        )
        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Phase 5.2 workspace order",
            status=Order.Status.ASSIGNED,
        )
        category = EditCategory.objects.create(
            title="Phase 5.2 category",
            slug="phase-52-category",
        )
        style = EditStyle.objects.create(
            category=category,
            title="Phase 5.2 style",
            slug="phase-52-style",
        )
        self.project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Phase 5.2 project",
            edit_style=style,
        )

    def test_order_workspace_for_participants_and_staff(self):
        for user in [self.client_user, self.editor_user, self.staff_user]:
            self.client.force_login(user)
            response = self.client.get(
                reverse("control_panel:order_detail", args=[self.order.pk])
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "پیشرفت واقعی Workflow")
            self.assertContains(response, "Timeline")
            self.assertContains(response, "تحویل‌ها")

    def test_project_workspace_for_owner_and_staff(self):
        for user in [self.client_user, self.staff_user]:
            self.client.force_login(user)
            response = self.client.get(
                reverse("control_panel:project_detail", args=[self.project.pk])
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "پیشرفت Workflow پروژه")
            self.assertContains(response, "پیشنهادها")
