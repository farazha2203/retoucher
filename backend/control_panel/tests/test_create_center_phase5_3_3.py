from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import EditorProfile
from catalog.models import EditCategory, EditPackage, EditStyle
from orders.models import Order
from projects.models import ProjectRequest, ProjectRequestActivity


class PanelCreateCenterTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase533_client",
            password="StrongPass123!",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="phase533_editor",
            password="StrongPass123!",
            role="editor",
        )
        self.admin_user = User.objects.create_user(
            username="phase533_admin",
            password="StrongPass123!",
            role="admin",
            is_staff=True,
        )
        self.category = EditCategory.objects.create(
            title="Phase 533",
            slug="phase-533",
            is_active=True,
        )
        self.style = EditStyle.objects.create(
            category=self.category,
            title="Beauty",
            slug="phase-533-beauty",
            is_active=True,
        )
        self.package = EditPackage.objects.create(
            style=self.style,
            title="Standard",
            level=EditPackage.PackageLevel.STANDARD,
            price=250000,
            is_active=True,
        )
        self.editor_profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name="Phase 533 Editor",
            is_available=True,
            accepts_direct_requests=True,
        )
        self.editor_profile.skills.add(self.style)

    def test_client_can_create_order_through_real_viewset(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse("control_panel:order_create"),
            {
                "title": "سفارش تست پنل",
                "description": "شرح سفارش",
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(title="سفارش تست پنل")
        self.assertEqual(order.client, self.client_user)
        self.assertEqual(order.status, Order.Status.DRAFT)

    def test_non_client_cannot_open_order_create(self):
        for user in [self.editor_user, self.admin_user]:
            self.client.force_login(user)
            response = self.client.get(
                reverse("control_panel:order_create")
            )
            self.assertEqual(response.status_code, 403)

    def test_client_can_create_managed_project_through_real_viewset(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse("control_panel:project_create"),
            {
                "request_type": ProjectRequest.RequestType.MANAGED_ORDER,
                "title": "پروژه مدیریت‌شده پنل",
                "description": "شرح پروژه",
                "edit_style": self.style.pk,
                "package": self.package.pk,
                "budget_min": 100000,
                "budget_max": 500000,
            },
        )
        self.assertEqual(response.status_code, 302)
        project = ProjectRequest.objects.get(
            title="پروژه مدیریت‌شده پنل"
        )
        self.assertEqual(project.client, self.client_user)
        self.assertEqual(
            project.status,
            ProjectRequest.Status.SUBMITTED,
        )
        self.assertTrue(
            ProjectRequestActivity.objects.filter(
                project_request=project,
                action=ProjectRequestActivity.Action.CREATED,
            ).exists()
        )

    def test_client_can_create_direct_editor_project(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse("control_panel:project_create"),
            {
                "request_type": ProjectRequest.RequestType.DIRECT_EDITOR,
                "title": "پروژه مستقیم پنل",
                "edit_style": self.style.pk,
                "target_editor": self.editor_profile.pk,
                "budget_min": 100000,
                "budget_max": 300000,
            },
        )
        self.assertEqual(response.status_code, 302)
        project = ProjectRequest.objects.get(title="پروژه مستقیم پنل")
        self.assertEqual(
            project.status,
            ProjectRequest.Status.WAITING_FOR_EDITOR,
        )
        self.assertEqual(project.target_editor, self.editor_profile)

    def test_invalid_package_style_is_shown_in_form(self):
        other_style = EditStyle.objects.create(
            category=self.category,
            title="Other",
            slug="phase-533-other",
            is_active=True,
        )
        other_package = EditPackage.objects.create(
            style=other_style,
            title="Other package",
            price=100,
            is_active=True,
        )
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse("control_panel:project_create"),
            {
                "request_type": ProjectRequest.RequestType.MANAGED_ORDER,
                "title": "Invalid project",
                "edit_style": self.style.pk,
                "package": other_package.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "بسته انتخابی باید متعلق به سبک انتخاب‌شده باشد.",
        )
        self.assertFalse(
            ProjectRequest.objects.filter(title="Invalid project").exists()
        )
