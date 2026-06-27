from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from orders.models import Order, OrderActivityLog, OrderImage, OrderStatusHistory


from accounts.models import EditorProfile
from catalog.models import EditCategory, EditPackage, EditStyle
from .models import (
    ProjectProposal,
    ProjectRequest,
    ProjectRequestActivity,
    ProjectRequestImage,
)


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
        self.assertEqual(response.data["status"], ProjectRequest.Status.SUBMITTED)
        self.assertIn("submitted_at", response.data)
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
        self.assertEqual(
            response.data["status"], ProjectRequest.Status.WAITING_FOR_EDITOR
        )
        self.assertIn("submitted_at", response.data)
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
        self.assertEqual(response.data["status"], ProjectRequest.Status.OPEN_FOR_QUOTES)
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
            response.data["status"], ProjectRequest.Status.OPEN_FOR_SAMPLES
        )
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

    def test_editor_can_list_matching_sample_challenge_request(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample challenge request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.get("/api/projects/requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], project_request.id)

    def test_editor_can_submit_sample_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample challenge request",
            edit_style=self.style,
        )

        sample_file = SimpleUploadedFile(
            "sample.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/sample-proposal/",
            {
                "proposed_price": 450000,
                "editor_fee": 320000,
                "estimated_delivery_hours": 48,
                "editor_note": "I edited the sample with natural skin texture.",
                "sample_note": "Skin cleanup, color balance, and natural contrast.",
                "sample_file": sample_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectProposal.objects.count(), 1)

        proposal = ProjectProposal.objects.first()
        self.assertEqual(proposal.status, ProjectProposal.Status.UNDER_REVIEW)
        self.assertFalse(proposal.is_visible_to_client)

    def test_staff_can_approve_sample_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample challenge request",
            edit_style=self.style,
        )

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            sample_file="project_proposals/samples/sample.jpg",
            is_visible_to_client=False,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/proposals/{proposal.id}/review-sample/",
            {
                "action": "approve",
                "supervisor_score": 9,
                "supervisor_note": "Good natural retouch with realistic skin texture.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, ProjectProposal.Status.APPROVED)
        self.assertEqual(proposal.supervisor_score, 9)
        self.assertTrue(proposal.is_visible_to_client)
        self.assertEqual(proposal.reviewed_by, self.staff_user)

    def test_staff_can_reject_sample_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample challenge request",
            edit_style=self.style,
        )

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            sample_file="project_proposals/samples/sample.jpg",
            is_visible_to_client=False,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/proposals/{proposal.id}/review-sample/",
            {
                "action": "reject",
                "supervisor_note": "Over-smoothed skin.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, ProjectProposal.Status.REJECTED_BY_SUPERVISOR)
        self.assertFalse(proposal.is_visible_to_client)

    def test_client_can_select_approved_sample_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample challenge request",
            edit_style=self.style,
        )

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.APPROVED,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            sample_file="project_proposals/samples/sample.jpg",
            supervisor_score=9,
            is_visible_to_client=True,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/proposals/{proposal.id}/select/",
            {
                "client_note": "I choose this sample edit.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposal.refresh_from_db()
        project_request.refresh_from_db()

        self.assertEqual(proposal.status, ProjectProposal.Status.ACCEPTED_BY_CLIENT)
        self.assertEqual(project_request.status, ProjectRequest.Status.EDITOR_SELECTED)
        self.assertEqual(project_request.target_editor, self.editor_profile)

    def test_client_cannot_select_unapproved_sample_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample challenge request",
            edit_style=self.style,
        )

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            sample_file="project_proposals/samples/sample.jpg",
            is_visible_to_client=False,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/proposals/{proposal.id}/select/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_can_convert_selected_direct_project_request_to_order(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Selected direct request",
            description="Direct project description",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=350000,
            editor_fee=250000,
            estimated_delivery_hours=24,
            editor_note="I can do this work.",
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {
                "note": "Client confirms conversion.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        project_request.refresh_from_db()

        self.assertEqual(order.client, self.client_user)
        self.assertEqual(order.editor, self.editor_user)
        self.assertEqual(order.status, Order.Status.ASSIGNED)
        self.assertEqual(order.title, "Selected direct request")
        self.assertIsNotNone(order.deadline)

        self.assertEqual(
            project_request.status, ProjectRequest.Status.CONVERTED_TO_ORDER
        )
        self.assertEqual(project_request.converted_order, order)

        self.assertEqual(OrderStatusHistory.objects.count(), 1)
        self.assertEqual(OrderActivityLog.objects.count(), 1)

    def test_client_can_convert_selected_public_quote_request_to_order(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Selected public quote",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.ACCEPTED_BY_CLIENT,
            proposed_price=300000,
            editor_fee=220000,
            estimated_delivery_hours=36,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.editor, self.editor_user)
        self.assertEqual(order.status, Order.Status.ASSIGNED)

    def test_cannot_convert_project_request_without_selected_editor(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Not selected request",
            edit_style=self.style,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_cannot_convert_public_quote_without_accepted_proposal(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Public without accepted proposal",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=300000,
            editor_fee=220000,
            estimated_delivery_hours=24,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_cannot_convert_project_request_twice(self):
        order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Existing order",
            status=Order.Status.ASSIGNED,
        )

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Already converted request",
            edit_style=self.style,
            target_editor=self.editor_profile,
            converted_order=order,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 1)

    def test_other_client_cannot_convert_project_request(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Other client should not convert",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        self.client.force_authenticate(user=self.other_client)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Order.objects.count(), 0)

    def test_staff_can_convert_project_request_to_order(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Staff conversion request",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=350000,
            editor_fee=250000,
            estimated_delivery_hours=24,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

    def test_project_request_images_are_copied_to_order_images(self):
        from .models import ProjectRequestImage

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.EDITOR_SELECTED,
            title="Request with images",
            edit_style=self.style,
            target_editor=self.editor_profile,
        )

        ProjectRequestImage.objects.create(
            project_request=project_request,
            image="project_requests/originals/test.jpg",
            caption="Original image",
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=350000,
            editor_fee=250000,
            estimated_delivery_hours=24,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrderImage.objects.count(), 1)

        order_image = OrderImage.objects.first()
        self.assertEqual(order_image.note, "Original image")

    def test_staff_can_managed_assign_editor_to_project_request(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Managed request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/managed-assign/",
            {
                "editor": self.editor_profile.id,
                "proposed_price": 400000,
                "editor_fee": 280000,
                "estimated_delivery_hours": 36,
                "editor_note": "Assigned by support for natural beauty retouch.",
                "support_note": "Editor selected based on skill and availability.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ProjectProposal.objects.count(), 1)

        proposal = ProjectProposal.objects.first()
        project_request.refresh_from_db()

        self.assertEqual(proposal.status, ProjectProposal.Status.ACCEPTED_BY_CLIENT)
        self.assertEqual(proposal.editor, self.editor_profile)
        self.assertEqual(proposal.proposed_price, 400000)
        self.assertEqual(proposal.editor_fee, 280000)

        self.assertEqual(project_request.status, ProjectRequest.Status.EDITOR_SELECTED)
        self.assertEqual(project_request.target_editor, self.editor_profile)
        self.assertIn("Editor selected", project_request.support_note)

    def test_client_cannot_managed_assign_editor(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Managed request",
            edit_style=self.style,
        )

        self.authenticate_client()
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/managed-assign/",
            {
                "editor": self.editor_profile.id,
                "proposed_price": 400000,
                "editor_fee": 280000,
                "estimated_delivery_hours": 36,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProjectProposal.objects.count(), 0)

    def test_managed_assign_requires_matching_editor_skill(self):
        other_category = EditCategory.objects.create(
            title="Product Photo",
            slug="product-photo-managed",
            sort_order=2,
        )
        other_style = EditStyle.objects.create(
            category=other_category,
            title="Product Cleanup",
            slug="product-cleanup-managed",
            min_price=50000,
            max_price=250000,
            suggested_price=120000,
            estimated_delivery_hours=12,
        )

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Managed product request",
            edit_style=other_style,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/managed-assign/",
            {
                "editor": self.editor_profile.id,
                "proposed_price": 400000,
                "editor_fee": 280000,
                "estimated_delivery_hours": 36,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("editor", response.data)
        self.assertEqual(ProjectProposal.objects.count(), 0)

    def test_managed_assign_can_be_converted_to_order(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.MANAGED_ORDER,
            status=ProjectRequest.Status.SUBMITTED,
            title="Managed request to convert",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.staff_user)
        assign_response = self.client.post(
            f"/api/projects/requests/{project_request.id}/managed-assign/",
            {
                "editor": self.editor_profile.id,
                "proposed_price": 400000,
                "editor_fee": 280000,
                "estimated_delivery_hours": 36,
                "support_note": "Ready to convert.",
            },
            format="json",
        )

        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)

        self.authenticate_client()
        convert_response = self.client.post(
            f"/api/projects/requests/{project_request.id}/convert-to-order/",
            {},
            format="json",
        )

        self.assertEqual(convert_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        project_request.refresh_from_db()

        self.assertEqual(order.client, self.client_user)
        self.assertEqual(order.editor, self.editor_user)
        self.assertEqual(order.status, Order.Status.ASSIGNED)
        self.assertEqual(
            project_request.status, ProjectRequest.Status.CONVERTED_TO_ORDER
        )

    def test_client_cannot_see_under_review_sample_proposal_in_detail(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample visibility request",
            edit_style=self.style,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            is_visible_to_client=False,
        )

        self.authenticate_client()
        response = self.client.get(f"/api/projects/requests/{project_request.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["proposals"], [])

    def test_client_can_see_approved_sample_proposal_in_detail(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Approved sample visibility request",
            edit_style=self.style,
        )

        proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.APPROVED,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            supervisor_score=9,
            is_visible_to_client=True,
        )

        self.authenticate_client()
        response = self.client.get(f"/api/projects/requests/{project_request.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["proposals"]), 1)
        self.assertEqual(response.data["proposals"][0]["id"], proposal.id)

    def test_staff_can_see_all_proposals_in_detail(self):
        other_editor_user = get_user_model().objects.create_user(
            username="staff_visibility_editor",
            password="EditorPass123!",
        )
        other_editor_profile = EditorProfile.objects.create(
            user=other_editor_user,
            display_name="Staff Visibility Editor",
            is_available=True,
            accepts_public_requests=True,
            accepts_sample_challenges=True,
        )
        other_editor_profile.skills.add(self.style)

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Staff visibility request",
            edit_style=self.style,
        )

        hidden = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            proposed_price=450000,
            editor_fee=320000,
            estimated_delivery_hours=48,
            is_visible_to_client=False,
        )

        approved = ProjectProposal.objects.create(
            project_request=project_request,
            editor=other_editor_profile,
            status=ProjectProposal.Status.APPROVED,
            proposed_price=500000,
            editor_fee=350000,
            estimated_delivery_hours=48,
            supervisor_score=9,
            is_visible_to_client=True,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f"/api/projects/requests/{project_request.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposal_ids = {item["id"] for item in response.data["proposals"]}
        self.assertEqual(proposal_ids, {hidden.id, approved.id})

    def test_editor_only_sees_own_proposals_in_detail(self):
        other_editor_user = get_user_model().objects.create_user(
            username="visibility_editor",
            password="EditorPass123!",
        )
        other_editor_profile = EditorProfile.objects.create(
            user=other_editor_user,
            display_name="Visibility Editor",
            is_available=True,
            accepts_public_requests=True,
            accepts_sample_challenges=True,
        )
        other_editor_profile.skills.add(self.style)

        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Editor visibility request",
            edit_style=self.style,
        )

        own_proposal = ProjectProposal.objects.create(
            project_request=project_request,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=300000,
            editor_fee=220000,
            estimated_delivery_hours=24,
        )

        ProjectProposal.objects.create(
            project_request=project_request,
            editor=other_editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=280000,
            editor_fee=200000,
            estimated_delivery_hours=36,
        )

        self.client.force_authenticate(user=self.editor_user)
        response = self.client.get(f"/api/projects/requests/{project_request.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["proposals"]), 1)
        self.assertEqual(response.data["proposals"][0]["id"], own_proposal.id)

    def test_staff_can_get_project_request_dashboard_summary(self):
        ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Dashboard public quote request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get("/api/projects/requests/dashboard-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_requests", response.data)
        self.assertIn("total_proposals", response.data)
        self.assertIn("requests_by_status", response.data)
        self.assertIn("requests_by_type", response.data)
        self.assertIn("proposals_by_status", response.data)
        self.assertIn("latest_requests", response.data)
        self.assertGreaterEqual(response.data["total_requests"], 1)

    def test_client_cannot_get_project_request_dashboard_summary(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get("/api/projects/requests/dashboard-summary/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_get_project_request_activities(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Activity log request",
            edit_style=self.style,
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Project request created.",
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            f"/api/projects/requests/{project_request.id}/activities/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["action"], ProjectRequestActivity.Action.CREATED
        )
        self.assertEqual(response.data[0]["actor"], self.client_user.id)

    def test_client_cannot_get_project_request_activities(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Private activity log request",
            edit_style=self.style,
        )

        self.client.force_authenticate(user=self.client_user)

        response = self.client.get(
            f"/api/projects/requests/{project_request.id}/activities/"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_get_latest_project_request_activities(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Latest activity request",
            edit_style=self.style,
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Project request created.",
            metadata={"source": "test"},
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get("/api/projects/requests/latest-activities/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["action"], ProjectRequestActivity.Action.CREATED
        )
        self.assertEqual(response.data[0]["project_request"], project_request.id)
        self.assertEqual(
            response.data[0]["project_request_title"], project_request.title
        )

    def test_client_cannot_get_latest_project_request_activities(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get("/api/projects/requests/latest-activities/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_filter_latest_project_request_activities_by_action(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Filtered latest activity request",
            edit_style=self.style,
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Project request created.",
            metadata={"source": "test"},
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.staff_user,
            action=ProjectRequestActivity.Action.MANAGED_ASSIGNED,
            message="Managed assignment completed.",
            metadata={"source": "test"},
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            "/api/projects/requests/latest-activities/",
            {"action": ProjectRequestActivity.Action.MANAGED_ASSIGNED},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["action"],
            ProjectRequestActivity.Action.MANAGED_ASSIGNED,
        )

    def test_staff_can_filter_latest_project_request_activities_by_project_request(
        self,
    ):
        first_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="First activity request",
            edit_style=self.style,
        )

        second_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Second activity request",
            edit_style=self.style,
        )

        ProjectRequestActivity.objects.create(
            project_request=first_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="First request created.",
        )

        ProjectRequestActivity.objects.create(
            project_request=second_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Second request created.",
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            "/api/projects/requests/latest-activities/",
            {"project_request": second_request.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["project_request"], second_request.id)
        self.assertEqual(
            response.data[0]["project_request_title"], second_request.title
        )

    def test_dashboard_summary_includes_project_request_activity_stats(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Dashboard activity stats request",
            edit_style=self.style,
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Project request created.",
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.staff_user,
            action=ProjectRequestActivity.Action.MANAGED_ASSIGNED,
            message="Managed assignment completed.",
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get("/api/projects/requests/dashboard-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_activities", response.data)
        self.assertIn("activities_by_action", response.data)
        self.assertGreaterEqual(response.data["total_activities"], 2)
        self.assertEqual(
            response.data["activities_by_action"][
                ProjectRequestActivity.Action.CREATED
            ],
            1,
        )
        self.assertEqual(
            response.data["activities_by_action"][
                ProjectRequestActivity.Action.MANAGED_ASSIGNED
            ],
            1,
        )

    def test_staff_can_filter_latest_project_request_activities_by_actor(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Actor filtered activity request",
            edit_style=self.style,
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.client_user,
            action=ProjectRequestActivity.Action.CREATED,
            message="Project request created by client.",
        )

        ProjectRequestActivity.objects.create(
            project_request=project_request,
            actor=self.staff_user,
            action=ProjectRequestActivity.Action.MANAGED_ASSIGNED,
            message="Managed assignment by staff.",
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            "/api/projects/requests/latest-activities/",
            {"actor": self.staff_user.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["actor"], self.staff_user.id)
        self.assertEqual(
            response.data[0]["action"],
            ProjectRequestActivity.Action.MANAGED_ASSIGNED,
        )

    def test_staff_can_limit_latest_project_request_activities(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Limited activity request",
            edit_style=self.style,
        )

        for index in range(3):
            ProjectRequestActivity.objects.create(
                project_request=project_request,
                actor=self.client_user,
                action=ProjectRequestActivity.Action.CREATED,
                message=f"Activity {index + 1}",
                metadata={"index": index + 1},
            )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            "/api/projects/requests/latest-activities/",
            {"limit": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_latest_project_request_activities_invalid_limit_falls_back_to_default(
        self,
    ):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Invalid limit activity request",
            edit_style=self.style,
        )

        for index in range(3):
            ProjectRequestActivity.objects.create(
                project_request=project_request,
                actor=self.client_user,
                action=ProjectRequestActivity.Action.CREATED,
                message=f"Activity {index + 1}",
                metadata={"index": index + 1},
            )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            "/api/projects/requests/latest-activities/",
            {"limit": "invalid"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_creating_project_request_creates_activity_log(self):
        self.client.force_authenticate(user=self.client_user)

        payload = {
            "request_type": ProjectRequest.RequestType.PUBLIC_QUOTE,
            "title": "Activity auto created request",
            "description": "Please retouch this project naturally.",
            "edit_style": self.style.id,
            "package": self.package.id,
            "budget_min": "200000.00",
            "budget_max": "700000.00",
            "deadline": "2026-06-28T20:26:20Z",
        }

        response = self.client.post(
            "/api/projects/requests/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        project_request = ProjectRequest.objects.get(
            id=response.data["id"],
        )

        activity = ProjectRequestActivity.objects.filter(
            project_request=project_request,
            action=ProjectRequestActivity.Action.CREATED,
        ).first()

        self.assertIsNotNone(activity)
        self.assertEqual(activity.actor, self.client_user)
        self.assertEqual(
            activity.metadata["request_type"], project_request.request_type
        )
        self.assertEqual(activity.metadata["status"], project_request.status)

    def test_uploading_project_request_image_creates_activity_log(self):
        project_request = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title="Image upload activity request",
            description="Request with image upload activity.",
            edit_style=self.style,
            package=self.package,
        )

        image = SimpleUploadedFile(
            "sample.png",
            (
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01"
                b"\x00\x00\x00\x01"
                b"\x08\x02\x00\x00\x00"
                b"\x90wS\xde"
                b"\x00\x00\x00\x0cIDAT"
                b"\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe"
                b"\xdc\xccY\xe7"
                b"\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            content_type="image/png",
        )

        self.client.force_authenticate(user=self.client_user)

        response = self.client.post(
            f"/api/projects/requests/{project_request.id}/images/",
            {
                "image": image,
                "caption": "Before retouch sample",
                "is_sample_image": True,
                "sort_order": 1,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        activity = ProjectRequestActivity.objects.filter(
            project_request=project_request,
            action=ProjectRequestActivity.Action.IMAGE_UPLOADED,
        ).first()

        self.assertIsNotNone(activity)
        self.assertEqual(activity.actor, self.client_user)
        self.assertIn("image_id", activity.metadata)
