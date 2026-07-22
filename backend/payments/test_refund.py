"""
Tests for refund functionality.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order
from payments.refund_models import Refund, RefundEvidence
from accounts.models import EditorProfile

User = get_user_model()


class RefundTests(TestCase):

    def setUp(self):
        self.api_client = APIClient()  # ✅ api_client نه client

        self.client_user = User.objects.create_user(
            username='client_u', password='TestPass123!', email='client@test.com',
        )
        self.editor_user = User.objects.create_user(
            username='editor_u', password='TestPass123!', email='editor@test.com',
        )
        self.admin_user = User.objects.create_user(
            username='admin_u', password='TestPass123!', email='admin@test.com',
            is_staff=True,
        )
        self.editor_profile = EditorProfile.objects.create(
            user=self.editor_user, display_name='Test Editor',
        )
        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title='Test Order',
            status=Order.Status.COMPLETED,
            agreed_price=500000,
            closed_at=timezone.now(),
        )

    def test_client_can_request_refund(self):
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            '/api/payments/refunds/',
            {
                'order_id': self.order.id,
                'reason': 'dispute',
                'description': 'Not as expected',
                'requested_amount': 400000,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'requested')
        refund = Refund.objects.get(order=self.order)
        self.assertEqual(refund.requested_amount, 400000)

    def test_cannot_request_multiple_refunds(self):
        Refund.objects.create(
            order=self.order,
            reason='dispute',
            requested_amount=400000,
            requested_by=self.client_user,
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            '/api/payments/refunds/',
            {'order_id': self.order.id, 'reason': 'dispute', 'requested_amount': 200000},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_approve_refund(self):
        refund = Refund.objects.create(
            order=self.order, reason='dispute',
            requested_amount=400000, requested_by=self.client_user,
        )
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            f'/api/payments/refunds/{refund.id}/approve/',
            {'approved_amount': 350000, 'note': 'Approved'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refund.refresh_from_db()
        self.assertEqual(refund.status, 'approved')
        self.assertEqual(refund.approved_amount, 350000)

    def test_admin_can_reject_refund(self):
        refund = Refund.objects.create(
            order=self.order, reason='dispute',
            requested_amount=400000, requested_by=self.client_user,
        )
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            f'/api/payments/refunds/{refund.id}/reject/',
            {'note': 'Insufficient evidence'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refund.refresh_from_db()
        self.assertEqual(refund.status, 'rejected')

    def test_client_can_upload_evidence(self):
        refund = Refund.objects.create(
            order=self.order, reason='dispute',
            requested_amount=400000, requested_by=self.client_user,
        )
        self.api_client.force_authenticate(user=self.client_user)
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_file = SimpleUploadedFile("evidence.txt", b"file_content", content_type="text/plain")
        response = self.api_client.post(
            f'/api/payments/refunds/{refund.id}/evidence/',
            {'file': test_file, 'description': 'Screenshot'},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RefundEvidence.objects.filter(refund=refund).exists())

    def test_non_admin_cannot_approve(self):
        refund = Refund.objects.create(
            order=self.order, reason='dispute',
            requested_amount=400000, requested_by=self.client_user,
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.post(
            f'/api/payments/refunds/{refund.id}/approve/',
            {'note': 'trying'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_can_list_own_refunds(self):
        Refund.objects.create(
            order=self.order, reason='dispute',
            requested_amount=400000, requested_by=self.client_user,
        )
        self.api_client.force_authenticate(user=self.client_user)
        response = self.api_client.get('/api/payments/refunds/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)