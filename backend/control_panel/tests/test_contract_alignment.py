from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import EditorProfile
from catalog.models import EditCategory, EditStyle
from orders.models import Order
from projects.models import ProjectProposal, ProjectRequest

from control_panel.access import (
    can_view_order,
    can_view_project,
    visible_orders,
    visible_project_proposals,
    visible_projects,
)
from control_panel.contracts import order_actions, project_actions


class ContractAlignedPanelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user("panel_client", role="client")
        self.other_client = User.objects.create_user("panel_other", role="client")
        self.editor_user = User.objects.create_user("panel_editor", role="editor")
        self.support = User.objects.create_user("panel_support", role="support")
        self.supervisor = User.objects.create_user("panel_supervisor", role="supervisor")
        self.staff = User.objects.create_user("panel_staff", role="admin", is_staff=True)

        category = EditCategory.objects.create(title="Panel", slug="panel-contract")
        self.style = EditStyle.objects.create(
            category=category,
            title="Panel style",
            slug="panel-style",
            is_active=True,
        )
        self.editor_profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name="Panel editor",
        )
        self.editor_profile.skills.add(self.style)

    def test_order_visibility_matches_order_viewset_contract(self):
        owned = Order.objects.create(client=self.client_user, title="Owned")
        assigned = Order.objects.create(
            client=self.other_client,
            editor=self.editor_user,
            title="Assigned",
        )
        hidden = Order.objects.create(client=self.other_client, title="Hidden")

        self.assertEqual(
            set(visible_orders(self.client_user, Order.objects.all())),
            {owned},
        )
        self.assertEqual(
            set(visible_orders(self.editor_user, Order.objects.all())),
            {assigned},
        )
        self.assertEqual(
            set(visible_orders(self.support, Order.objects.all())),
            {owned, assigned, hidden},
        )
        self.assertTrue(can_view_order(self.supervisor, hidden))
        self.assertFalse(can_view_order(self.client_user, hidden))

    def test_project_visibility_matches_project_viewset_contract(self):
        own = ProjectRequest.objects.create(
            client=self.client_user,
            edit_style=self.style,
            title="Own",
        )
        public = ProjectRequest.objects.create(
            client=self.other_client,
            edit_style=self.style,
            title="Public",
            request_type="public_quote",
            status="open_for_quotes",
        )
        hidden = ProjectRequest.objects.create(
            client=self.other_client,
            edit_style=self.style,
            title="Hidden",
        )

        self.assertEqual(
            set(visible_projects(self.client_user, ProjectRequest.objects.all())),
            {own},
        )
        self.assertIn(
            public,
            visible_projects(self.editor_user, ProjectRequest.objects.all()),
        )
        self.assertNotIn(
            hidden,
            visible_projects(self.editor_user, ProjectRequest.objects.all()),
        )
        self.assertTrue(can_view_project(self.staff, hidden))

    def test_client_and_editor_proposal_visibility_matches_serializer(self):
        project = ProjectRequest.objects.create(
            client=self.client_user,
            edit_style=self.style,
            title="Quotes",
            request_type="sample_challenge",
            status="open_for_samples",
        )
        approved = ProjectProposal.objects.create(
            project_request=project,
            editor=self.editor_profile,
            status="approved",
            is_visible_to_client=True,
        )
        hidden = ProjectProposal.objects.create(
            project_request=project,
            editor=EditorProfile.objects.create(
                user=get_user_model().objects.create_user("other_editor", role="editor")
            ),
            status="under_review",
            is_visible_to_client=False,
        )

        client_qs = visible_project_proposals(
            self.client_user,
            project,
            project.proposals.all(),
        )
        editor_qs = visible_project_proposals(
            self.editor_user,
            project,
            project.proposals.all(),
        )

        self.assertIn(approved, client_qs)
        self.assertNotIn(hidden, client_qs)
        self.assertEqual(set(editor_qs), {approved})

    def test_order_actions_are_state_and_actor_specific(self):
        order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Workflow",
            status="assigned",
        )
        self.assertEqual(
            [item.key for item in order_actions(self.editor_user, order)],
            ["start_work"],
        )
        self.assertEqual(order_actions(self.client_user, order), [])

    def test_project_actions_are_state_and_actor_specific(self):
        project = ProjectRequest.objects.create(
            client=self.other_client,
            edit_style=self.style,
            title="Opportunity",
            request_type="public_quote",
            status="open_for_quotes",
        )
        self.assertEqual(
            [item.key for item in project_actions(self.editor_user, project)],
            ["public_proposal"],
        )
