from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import EditorProfile
from catalog.models import EditCategory, EditPackage, EditStyle
from .models import ProjectProposal, ProjectRequest


class ProjectRequestAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="client_test",
            password="ClientPass123!",
            email="client@example.com",
        )
        self.other_client = User.objects.create_user(
            username="other_client",
            password="ClientPass123!",
            email="other@example.com",
        )
        self.staff_user = User.objects.create_user(
            username="support_test",
            password="SupportPass123!",
            email="support@example.com",
            is_staff=True,
        )
        self.editor_user = User.objects.create_user(
            username="editor_test",
            password="EditorPass123!",
            email="editor@example.com",
        )

        self.category = EditCategory.objects.create(
            title="Beauty Retouch",
            slug="beauty-retouch",
            sort_order=1,
        )
        self.style = EditStyle.objects.create(
            category=self.category,
            title="Natural Beauty",
            slug="natural-beauty",
            min_price=100000,
            max_price=500000,
            suggested_price=250000,
            estimated_delivery_hours=24,
        )
        self.package = EditPackage.objects.create(
            style=self.style,
            title="Standard",
            level=EditPackage.PackageLevel.STANDARD,
            price=250000,
            min_images=1,
            max_images=3,
            estimated_delivery_hours=24,
        )

        self.editor_profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name="Editor Test",
            level=EditorProfile.EditorLevel.SENIOR,
            is_available=True,
            accepts_direct_requests=True,
        )
        self.editor_profile.skills.add(self.style)

    def authenticate_client(self):
        self.client.force_authenticate(user=self.client_user)

    def test_client_can_create_managed_project_request(self):
        self.authenticate_client()

        response = self.client.post(
            "/api/projects/requests/",
            {
                "request_type": ProjectRequest.RequestType.MANAGED_ORDER,
                "title": "My beauty project",
                "description": "Please retouch these images.",
                "edit_style": self.style.id,
                "package": self.package.id,
                "budget_min": 100000,
                "budget_max": 500000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectRequest.objects.count(), 1)
        project_request = ProjectRequest.objects.first()
        self.assertEqual(project_request.client, self.client_user)
        self.assertEqual(project_request.status, ProjectRequest.Status.SUBMITTED)

    def test_direct_editor_request_requires_target_editor(self):
        self.authenticate_client()

        response = self.client.post(
            "/api/projects/requests/",
            {
                "request_type": ProjectRequest.RequestType.DIRECT_EDITOR,
                "title": "Direct request",
                "edit_style": self.style.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target_editor", response.data)

    def test_client_can_create_direct_editor_request(self):
        self.authenticate_client()

        response = self.client.post(
            "/api/projects/requests/",
            {
                "request_type": ProjectRequest.RequestType.DIRECT_EDITOR,
                "title": "Direct request",
                "edit_style": self.style.id,
                "target_editor": self.editor_profile.id,
                "budget_min": 100000,
                "budget_max": 500000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_request = ProjectRequest.objects.first()
        self.assertEqual(
            project_request.status, ProjectRequest.Status.WAITING_FOR_EDITOR
        )
        self.assertEqual(project_request.target_editor, self.editor_profile)

    def test_public_quote_request_opens_for_quotes(self):
        self.authenticate_client()

        response = self.client.post(
            "/api/projects/requests/",
            {
                "request_type": ProjectRequest.RequestType.PUBLIC_QUOTE,
                "title": "Public quote",
                "edit_style": self.style.id,
                "budget_min": 100000,
                "budget_max": 500000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ProjectRequest.objects.first().status,
            ProjectRequest.Status.OPEN_FOR_QUOTES,
        )

    def test_sample_challenge_request_opens_for_samples(self):
        self.authenticate_client()

        response = self.client.post(
            "/api/projects/requests/",
            {
                "request_type": ProjectRequest.RequestType.SAMPLE_CHALLENGE,
                "title": "Sample challenge",
                "edit_style": self.style.id,
                "budget_min": 100000,
                "budget_max": 500000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ProjectRequest.objects.first().status,
            ProjectRequest.Status.OPEN_FOR_SAMPLES,
        )

    def test_client_only_lists_own_requests(self):
        ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Own request",
            edit_style=self.style,
        )
        ProjectRequest.objects.create(
            client=self.other_client,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Other request",
            edit_style=self.style,
        )

        self.authenticate_client()
        response = self.client.get("/api/projects/requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Own request")

    def test_staff_can_list_all_requests(self):
        ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Client request",
            edit_style=self.style,
        )
        ProjectRequest.objects.create(
            client=self.other_client,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Other request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/projects/requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_package_must_belong_to_selected_style(self):
        other_category = EditCategory.objects.create(
            title="Product Photo",
            slug="product-photo",
            sort_order=2,
        )
        other_style = EditStyle.objects.create(
            category=other_category,
            title="Background Cleanup",
            slug="background-cleanup",
            min_price=50000,
            max_price=250000,
            suggested_price=120000,
            estimated_delivery_hours=12,
        )

        self.authenticate_client()

        response = self.client.post(
            "/api/projects/requests/",
            {
                "request_type": ProjectRequest.RequestType.MANAGED_ORDER,
                "title": "Invalid package",
                "edit_style": other_style.id,
                "package": self.package.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("package", response.data)

    def test_target_editor_can_list_direct_request(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.WAITING_FOR_EDITOR,
            title="Direct request",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.get("/api/projects/requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], project_request.id)

    def test_target_editor_can_submit_direct_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.WAITING_FOR_EDITOR,
            title="Direct request",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/direct-proposal/",
            {
                "proposed_price": 350000,
                "editor_fee": 250000,
                "estimated_delivery_hours": 24,
                "editor_note": "I can do a natural beauty retouch.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectProposal.objects.count(), 1)

        project_request.refresh_from_db()
        self.assertEqual(project_request.status, ProjectRequest.Status.EDITOR_SELECTED)

    def test_non_target_editor_cannot_submit_direct_proposal(self):
        other_editor_user = get_user_model().objects.create_user(
            username="other_editor",
            password="EditorPass123!",
        )
        other_editor_profile = EditorProfile.objects.create(
            user=other_editor_user,
            display_name="Other Editor",
            is_available=True,
            accepts_direct_requests=True,
        )
        other_editor_profile.skills.add(self.style)

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.WAITING_FOR_EDITOR,
            title="Direct request",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        self.client.force_authenticate(user=other_editor_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/direct-proposal/",
            {
                "proposed_price": 350000,
                "editor_fee": 250000,
                "estimated_delivery_hours": 24,
                "editor_note": "I want this job.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ProjectProposal.objects.count(), 0)

    def test_target_editor_can_decline_direct_request(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.WAITING_FOR_EDITOR,
            title="Direct request",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/direct-decline/",
            {
                "editor_note": "I am not available for this deadline.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ProjectProposal.objects.count(), 1)

        proposal = ProjectProposal.objects.first()
        self.assertEqual(proposal.status, ProjectProposal.Status.DECLINED_BY_EDITOR)

        project_request.refresh_from_db()
        self.assertEqual(project_request.status, ProjectRequest.Status.CANCELLED)


    def test_editor_can_list_matching_public_quote_request(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Public quote request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.get("/api/projects/requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], project_request.id)

    def test_editor_can_submit_public_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Public quote request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/public-proposal/",
            {
                "proposed_price": 300000,
                "editor_fee": 220000,
                "estimated_delivery_hours": 24,
                "editor_note": "I can do this with natural skin texture.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectProposal.objects.count(), 1)

        proposal = ProjectProposal.objects.first()
        self.assertEqual(proposal.proposed_price, 300000)
        self.assertEqual(proposal.status, ProjectProposal.Status.SUBMITTED)

    def test_editor_cannot_submit_duplicate_public_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Public quote request",
            edit_style=self.style,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            proposed_price=300000,
            editor_fee=220000,
            estimated_delivery_hours=24,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/public-proposal/",
            {
                "proposed_price": 350000,
                "editor_fee": 250000,
                "estimated_delivery_hours": 24,
                "editor_note": "Duplicate proposal.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ProjectProposal.objects.count(), 1)

    def test_client_can_select_public_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Public quote request",
            edit_style=self.style,
        )

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            proposed_price=300000,
            editor_fee=220000,
            estimated_delivery_hours=24,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/proposals/{proposal.id}/select/",
            {
                "client_note": "I choose this editor.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposal.refresh_from_db()
        project_request.refresh_from_db()

        self.assertEqual(proposal.status, ProjectProposal.Status.ACCEPTED_BY_CLIENT)
        self.assertEqual(project_request.status, ProjectRequest.Status.EDITOR_SELECTED)
        self.assertEqual(project_request.target_editor, self.editor_profile)

    def test_selecting_one_public_proposal_rejects_others(self):
        other_editor_user = get_user_model().objects.create_user(
            username="other_public_editor",
            password="EditorPass123!",
        )
        other_editor_profile = EditorProfile.objects.create(
            user=other_editor_user,
            display_name="Other Public Editor",
            is_available=True,
            accepts_public_requests=True,
        )
        other_editor_profile.skills.add(self.style)

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Public quote request",
            edit_style=self.style,
        )

        selected = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            proposed_price=300000,
            editor_fee=220000,
            estimated_delivery_hours=24,
        )
        rejected = ProjectProposal.objects.create(
            project_request=project_request,
            editor=other_editor_profile,
            proposed_price=280000,
            editor_fee=200000,
            estimated_delivery_hours=36,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/proposals/{selected.id}/select/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        selected.refresh_from_db()
        rejected.refresh_from_db()

        self.assertEqual(selected.status, ProjectProposal.Status.ACCEPTED_BY_CLIENT)
        self.assertEqual(rejected.status, ProjectProposal.Status.REJECTED_BY_CLIENT)
