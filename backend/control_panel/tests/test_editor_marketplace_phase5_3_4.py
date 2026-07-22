from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import EditorPortfolioItem, EditorProfile
from catalog.models import EditCategory, EditStyle
from projects.models import ProjectProposal, ProjectRequest


GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
    b"\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00"
    b"\x00\x01\x00\x01\x00\x00\x02\x02D"
    b"\x01\x00;"
)


class EditorMarketplacePhase534Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase534_client",
            password="StrongPass123!",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="phase534_editor",
            password="StrongPass123!",
            role="editor",
        )
        self.staff_user = User.objects.create_user(
            username="phase534_staff",
            password="StrongPass123!",
            role="admin",
            is_staff=True,
        )
        self.category = EditCategory.objects.create(
            title="Retouch",
            slug="phase534-retouch",
            is_active=True,
        )
        self.style = EditStyle.objects.create(
            category=self.category,
            title="Beauty",
            slug="phase534-beauty",
            is_active=True,
        )
        self.profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name="Sample Editor",
            is_available=True,
            accepts_direct_requests=True,
            accepts_sample_challenges=True,
        )
        self.profile.skills.add(self.style)
        EditorPortfolioItem.objects.create(
            editor=self.profile,
            style=self.style,
            title="Before After",
            is_active=True,
        )
        self.project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            status=ProjectRequest.Status.OPEN_FOR_SAMPLES,
            title="Sample project",
            edit_style=self.style,
        )

    def test_client_can_view_editor_portfolio(self):
        self.client.force_login(self.client_user)
        response = self.client.get(
            reverse("control_panel:editor_detail", args=[self.profile.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Before After")
        self.assertContains(response, "درخواست مستقیم")

    def test_client_can_upload_sample_image(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse(
                "control_panel:project_upload_sample_image",
                args=[self.project.pk],
            ),
            {
                "image": SimpleUploadedFile(
                    "sample.gif",
                    GIF,
                    content_type="image/gif",
                ),
                "caption": "Sample source",
            },
        )
        self.assertEqual(response.status_code, 302)
        image = self.project.images.get()
        self.assertTrue(image.is_sample_image)

    def test_editor_sample_submission_is_available_in_contract(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(
            reverse(
                "control_panel:project_detail",
                args=[self.project.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ارسال نمونه ادیت")

    def test_staff_can_review_sample_and_client_can_see_approved(self):
        proposal = ProjectProposal.objects.create(
            project_request=self.project,
            editor=self.profile,
            status=ProjectProposal.Status.SUBMITTED,
            sample_file=SimpleUploadedFile(
                "edited.gif",
                GIF,
                content_type="image/gif",
            ),
        )
        self.project.status = ProjectRequest.Status.UNDER_REVIEW
        self.project.save(update_fields=["status", "updated_at"])

        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse(
                "control_panel:project_review_sample",
                args=[self.project.pk, proposal.pk],
            ),
            {
                "approved": "on",
                "supervisor_score": 9,
                "supervisor_note": "Good sample",
                "is_visible_to_client": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        proposal.refresh_from_db()
        self.assertEqual(
            proposal.status,
            ProjectProposal.Status.APPROVED,
        )
        self.assertTrue(proposal.is_visible_to_client)

        self.client.force_login(self.client_user)
        response = self.client.get(
            reverse(
                "control_panel:project_detail",
                args=[self.project.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مشاهده نمونه ادیت")
        self.assertContains(response, "انتخاب این ادیتور")
