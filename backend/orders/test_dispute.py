"""
Tests for dispute resolution functionality.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order
from orders.dispute_models import Dispute, DisputeMessage, DisputeEvidence
from accounts.models import EditorProfile

User = get_user_model()


class DisputeTests(TestCase):

    def setUp(self):
        self.api_client = APIClient()

        self.client_user = User.objects.create_user(
            username='client_d', password='Test123!', email='client_d@test.com'
        )
        self.editor_user = User.objects.create_user(
            username='editor_d', password='Test123!', email='editor_d@test.com'
        )
        self.admin_user = User.objects.create_user(
            username='admin_d', password='Test123!', email='admin_d@test.com',
            is_staff=True,
        )
        EditorProfile.objects.create(user=self.editor_user, display_name='Editor')

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title='Test Order',
            status=Order.Status.COMPLETED,
            agreed_price=500000,
            closed_at=timezone.now(),
        )

    def test_client_can_open_dispute(self):
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            '/api/orders/disputes/open/',
            {
                'order_id': self.order.id,
                'category': 'quality',
                'description': 'The delivered work did not match the requirements.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'open')
        self.assertTrue(Dispute.objects.filter(order=self.order).exists())

    def test_editor_can_open_dispute(self):
        self.api_client.force_authenticate(user=self.editor_user)
        response = self.api_client.post(
            '/api/orders/disputes/open/',
            {
                'order_id': self.order.id,
                'category': 'payment',
                'description': 'Client changed the scope without agreement.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_open_duplicate_dispute(self):
        Dispute.objects.create(
            order=self.order,
            initiated_by=self.client_user,
            category='quality',
            description='First dispute',
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            '/api/orders/disputes/open/',
            {'order_id': self.order.id, 'category': 'quality', 'description': 'Second dispute attempt.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_can_send_message(self):
        dispute = Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            f'/api/orders/disputes/{dispute.id}/message/',
            {'message': 'Here is my explanation for the dispute.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DisputeMessage.objects.filter(dispute=dispute).count(), 1)

    def test_editor_can_send_message(self):
        dispute = Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.editor_user)
        response = self.api_client.post(
            f'/api/orders/disputes/{dispute.id}/message/',
            {'message': 'I disagree, here is my response.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_resolve_dispute(self):
        dispute = Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            f'/api/orders/disputes/{dispute.id}/resolve/',
            {
                'resolution': 'favors_client',
                'note': 'Evidence supports client claim.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'resolved')
        self.assertEqual(dispute.resolution, 'favors_client')

    def test_admin_can_resolve_with_compromise(self):
        dispute = Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            f'/api/orders/disputes/{dispute.id}/resolve/',
            {
                'resolution': 'compromise',
                'note': 'Split the difference.',
                'refund_amount': 250000,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dispute.refresh_from_db()
        self.assertEqual(dispute.refund_amount, 250000)

    def test_non_admin_cannot_resolve(self):
        dispute = Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            f'/api/orders/disputes/{dispute.id}/resolve/',
            {'resolution': 'favors_client', 'note': 'I want full refund.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_can_upload_evidence(self):
        dispute = Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.client_user)
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile("evidence.txt", b"content", content_type="text/plain")
        response = self.api_client.post(
            f'/api/orders/disputes/{dispute.id}/upload_evidence/',
            {'file': f, 'description': 'Screenshot'},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DisputeEvidence.objects.filter(dispute=dispute).count(), 1)

    def test_client_can_list_own_disputes(self):
        Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.get('/api/orders/disputes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_stranger_cannot_see_dispute(self):
        stranger = User.objects.create_user(
            username='stranger_d', password='Test123!', email='stranger_d@test.com'
        )
        Dispute.objects.create(
            order=self.order, initiated_by=self.client_user,
            category='quality', description='Test dispute',
        )
        self.api_client.force_authenticate(user=stranger)
        response = self.api_client.get('/api/orders/disputes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)