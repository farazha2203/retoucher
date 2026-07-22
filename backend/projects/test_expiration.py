"""Tests for project request expiration functionality."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from catalog.models import EditCategory, EditStyle
from .models import ProjectRequest, ProjectProposal, ProjectRequestActivity
from accounts.models import EditorProfile
from .expiration_handler import ProjectExpirationHandler, ProposalDeadlineHandler

User = get_user_model()


class ProjectExpirationTests(TestCase):
    """Test automatic project request expiration."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client_test',
            password='ClientPass123!',
            email='client@test.com',
        )
        
        self.category = EditCategory.objects.create(
            title='Test Category',
            slug='test-category',
        )
        
        self.style = EditStyle.objects.create(
            category=self.category,
            title='Test Style',
            slug='test-style',
        )

    def test_direct_editor_request_expires_in_7_days(self):
        """Test that direct editor requests expire in 7 days."""
        project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.SUBMITTED,
            title='Test Request',
            edit_style=self.style,
            submitted_at=timezone.now() - timedelta(days=8),
        )
        
        expiration_date = ProjectExpirationHandler.get_expiration_date(project)
        self.assertIsNotNone(expiration_date)
        self.assertTrue(expiration_date < timezone.now())

    def test_check_and_expire_requests(self):
        """Test the expiration check handler."""
        old_project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.SUBMITTED,
            title='Old Request',
            edit_style=self.style,
            submitted_at=timezone.now() - timedelta(days=8),
            expires_at=timezone.now() - timedelta(days=1),
        )
        
        new_project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.SUBMITTED,
            title='New Request',
            edit_style=self.style,
            submitted_at=timezone.now() - timedelta(hours=1),
            expires_at=timezone.now() + timedelta(days=6),
        )
        
        expired_count = ProjectExpirationHandler.check_and_expire_requests()
        
        self.assertEqual(expired_count, 1)
        
        old_project.refresh_from_db()
        self.assertEqual(old_project.status, ProjectRequest.Status.EXPIRED)
        
        new_project.refresh_from_db()
        self.assertEqual(new_project.status, ProjectRequest.Status.SUBMITTED)

    def test_expiration_creates_activity_log(self):
        """Test that expiration creates activity log."""
        project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.DIRECT_EDITOR,
            status=ProjectRequest.Status.SUBMITTED,
            title='Test Request',
            edit_style=self.style,
            submitted_at=timezone.now() - timedelta(days=8),
            expires_at=timezone.now() - timedelta(days=1),
        )
        
        ProjectExpirationHandler.check_and_expire_requests()
        
        activity = ProjectRequestActivity.objects.filter(
            project_request=project,
            action=ProjectRequestActivity.Action.EXPIRED,
        ).first()
        
        self.assertIsNotNone(activity)


class ProposalDeadlineTests(TestCase):
    """Test proposal deadline handling."""

    def setUp(self):
        self.editor_user = User.objects.create_user(
            username='editor_test',
            password='EditorPass123!',
        )
        
        self.client_user = User.objects.create_user(
            username='client_test',
            password='ClientPass123!',
        )
        
        self.editor_profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name='Test Editor',
        )
        
        self.category = EditCategory.objects.create(
            title='Test Category',
            slug='test-category',
        )
        
        self.style = EditStyle.objects.create(
            category=self.category,
            title='Test Style',
            slug='test-style',
        )
        
        self.editor_profile.skills.add(self.style)

    def test_proposal_deadline_calculation(self):
        """Test proposal deadline is calculated correctly."""
        project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title='Test',
            edit_style=self.style,
        )
        
        proposal = ProjectProposal.objects.create(
            project_request=project,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=300000,
            editor_fee=250000,
        )
        
        deadline = ProposalDeadlineHandler.get_proposal_deadline(proposal)
        self.assertIsNotNone(deadline)
        
        # ✅ FIXED: use submitted_at
        expected = proposal.submitted_at + timedelta(hours=72)
        self.assertEqual(deadline, expected)

    def test_proposal_remaining_hours(self):
        """Test remaining hours calculation."""
        project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title='Test',
            edit_style=self.style,
        )
        
        # ✅ FIXED: use submitted_at instead of created_at
        now_minus_24h = timezone.now() - timedelta(hours=24)
        proposal = ProjectProposal.objects.create(
            project_request=project,
            editor=self.editor_profile,
            status=ProjectProposal.Status.SUBMITTED,
            proposed_price=300000,
            editor_fee=250000,
        )
        # manually set submitted_at
        ProjectProposal.objects.filter(id=proposal.id).update(submitted_at=now_minus_24h)
        proposal.refresh_from_db()
        
        remaining = ProposalDeadlineHandler.get_remaining_hours(proposal)
        
        # Should be approximately 48 hours
        self.assertGreater(remaining, 45)
        self.assertLess(remaining, 50)

    def test_auto_reject_old_proposals(self):
        """Test that old proposals are auto-rejected."""
        project = ProjectRequest.objects.create(
            client=self.client_user,
            request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
            status=ProjectRequest.Status.OPEN_FOR_QUOTES,
            title='Test',
            edit_style=self.style,
        )
        
        # ✅ FIXED: use submitted_at instead of created_at
        now_minus_96h = timezone.now() - timedelta(hours=96)
        proposal = ProjectProposal.objects.create(
            project_request=project,
            editor=self.editor_profile,
            status=ProjectProposal.Status.UNDER_REVIEW,
            proposed_price=300000,
            editor_fee=250000,
        )
        # manually set submitted_at
        ProjectProposal.objects.filter(id=proposal.id).update(submitted_at=now_minus_96h)
        proposal.refresh_from_db()
        
        rejected_count = ProjectExpirationHandler.check_and_reject_proposals()
        
        self.assertEqual(rejected_count, 1)
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, ProjectProposal.Status.REJECTED_BY_SUPERVISOR)