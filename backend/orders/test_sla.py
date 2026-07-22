"""
Tests for SLA and penalty functionality.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order
from orders.sla_models import DeliveryPenalty, SLAConfig
from payments.models import Transaction, Wallet
from orders.sla_handler import SLAHandler
from accounts.models import EditorProfile

User = get_user_model()


class SLAHandlerTests(TestCase):
    """Test SLA calculation logic."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client', password='Test123!', email='client@test.com'
        )
        self.editor_user = User.objects.create_user(
            username='editor', password='Test123!', email='editor@test.com'
        )
        EditorProfile.objects.create(user=self.editor_user, display_name='Editor')

        # Create default SLA config
        SLAConfig.objects.create(
            penalty_percent_per_day=Decimal('2.00'),
            max_penalty_percent=Decimal('20.00'),
            grace_period_hours=2,
        )

    def _make_order(self, deadline_offset_hours=-24, status=Order.Status.IN_PROGRESS):
        return Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title='Test Order',
            status=status,
            agreed_price=Decimal('500000'),
            deadline=timezone.now() + timedelta(hours=deadline_offset_hours),
        )

    def test_on_time_delivery_no_penalty(self):
        """Test that on-time delivery has no penalty."""
        order = self._make_order(deadline_offset_hours=24)  # Deadline in future

        result = SLAHandler.calculate_penalty(order)

        self.assertFalse(result['is_late'])
        self.assertEqual(result['penalty_amount'], Decimal('0'))

    def test_late_delivery_creates_penalty(self):
        """Test that late delivery creates a penalty."""
        order = self._make_order(deadline_offset_hours=-48)  # 2 days overdue

        result = SLAHandler.calculate_penalty(order)

        self.assertTrue(result['is_late'])
        self.assertGreater(result['days_late'], 0)
        self.assertGreater(result['penalty_amount'], 0)

    def test_penalty_calculation_is_correct(self):
        """Test penalty math."""
        order = self._make_order(deadline_offset_hours=-48)

        result = SLAHandler.calculate_penalty(order)

        # 2 days late × 2% per day = 4% penalty
        # 4% of 500000 = 20000 tomans
        self.assertEqual(result['days_late'], 2)
        expected_percent = Decimal('4.00')
        self.assertEqual(result['penalty_percent'], expected_percent)
        expected_amount = Decimal('500000') * expected_percent / 100
        self.assertEqual(result['penalty_amount'], expected_amount)

    def test_max_penalty_cap(self):
        """Test that penalty is capped at max_penalty_percent."""
        order = self._make_order(deadline_offset_hours=-720)  # 30 days late!

        result = SLAHandler.calculate_penalty(order)

        # Should be capped at 20%
        self.assertEqual(result['penalty_percent'], Decimal('20.00'))

    def test_check_order_creates_penalty_record(self):
        """Test that SLA check creates a DeliveryPenalty record."""
        order = self._make_order(deadline_offset_hours=-48)

        penalty = SLAHandler.check_order_and_create_penalty(order)

        self.assertIsNotNone(penalty)
        self.assertEqual(penalty.order, order)
        self.assertEqual(penalty.status, DeliveryPenalty.Status.PENDING)

    def test_no_duplicate_penalty(self):
        """Test that duplicate penalties are not created."""
        order = self._make_order(deadline_offset_hours=-48)

        penalty1 = SLAHandler.check_order_and_create_penalty(order)
        penalty2 = SLAHandler.check_order_and_create_penalty(order)

        self.assertIsNotNone(penalty1)
        self.assertIsNone(penalty2)
        self.assertEqual(DeliveryPenalty.objects.filter(order=order).count(), 1)

    def test_no_penalty_without_deadline(self):
        """Test that orders without deadline have no penalty."""
        order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title='Test',
            status=Order.Status.IN_PROGRESS,
            agreed_price=Decimal('500000'),
            deadline=None,
        )

        result = SLAHandler.calculate_penalty(order)
        self.assertFalse(result['is_late'])

    def test_check_all_late_orders(self):
        """Test bulk SLA check."""
        # Create 2 late orders
        order1 = self._make_order(deadline_offset_hours=-48)
        order2 = self._make_order(deadline_offset_hours=-72)

        late_count = SLAHandler.check_all_late_orders()

        self.assertEqual(late_count, 2)
        self.assertEqual(DeliveryPenalty.objects.count(), 2)

class PenaltyAPITests(TestCase):
    """Test penalty API endpoints."""

    def setUp(self):
        self.api_client = APIClient()  # ✅ تغییر نام

        self.editor_user = User.objects.create_user(
            username='editor', password='Test123!', email='editor@test.com'
        )
        self.admin_user = User.objects.create_user(
            username='admin', password='Test123!', email='admin@test.com',
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username='client_user', password='Test123!', email='client@test.com'
        )
        EditorProfile.objects.create(user=self.editor_user, display_name='Editor')
        self.wallet = Wallet.objects.create(
            user=self.editor_user,
            balance=Decimal('50000'),
            withdrawable_balance=Decimal('50000'),
        )

        SLAConfig.objects.create(
            penalty_percent_per_day=Decimal('2.00'),
            max_penalty_percent=Decimal('20.00'),
            grace_period_hours=2,
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title='Test Order',
            status=Order.Status.IN_PROGRESS,
            agreed_price=Decimal('500000'),
            deadline=timezone.now() - timedelta(days=2),
        )

        self.penalty = DeliveryPenalty.objects.create(
            order=self.order,
            editor=self.editor_user,
            penalty_type=DeliveryPenalty.PenaltyType.LATE_DELIVERY,
            order_amount=Decimal('500000'),
            penalty_amount=Decimal('20000'),
            penalty_percent=Decimal('4.00'),
            deadline=self.order.deadline,
            days_late=2,
        )

    def test_editor_can_see_own_penalties(self):
        self.api_client.force_authenticate(user=self.editor_user)
        response = self.api_client.get('/api/orders/penalties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_apply_penalty(self):
        self.api_client.force_authenticate(user=self.admin_user)   # ✅
        response = self.api_client.post(
            f'/api/orders/penalties/{self.penalty.id}/apply/',
            {'note': 'Applied after review'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.penalty.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(self.penalty.status, DeliveryPenalty.Status.APPLIED)
        self.assertEqual(self.wallet.balance, Decimal('30000'))
        self.assertEqual(self.wallet.withdrawable_balance, Decimal('30000'))

        transaction = Transaction.objects.get(
            wallet=self.wallet,
            tx_type=Transaction.TxType.PENALTY,
            order=self.order,
        )
        self.assertEqual(transaction.amount, Decimal('20000'))
        self.assertEqual(transaction.balance_before, Decimal('50000'))
        self.assertEqual(transaction.balance_after, Decimal('30000'))
        self.assertEqual(transaction.status, Transaction.Status.SUCCESS)

    def test_apply_penalty_with_insufficient_earnings_is_rejected(self):
        self.wallet.balance = Decimal('0')
        self.wallet.withdrawable_balance = Decimal('0')
        self.wallet.save(update_fields=['balance', 'withdrawable_balance'])

        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            f'/api/orders/penalties/{self.penalty.id}/apply/',
            {'note': 'Should not overdraw wallet'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.penalty.refresh_from_db()
        self.assertEqual(self.penalty.status, DeliveryPenalty.Status.PENDING)
        self.assertFalse(
            Transaction.objects.filter(
                wallet=self.wallet,
                tx_type=Transaction.TxType.PENALTY,
                order=self.order,
            ).exists()
        )

    def test_admin_can_waive_penalty(self):
        self.api_client.force_authenticate(user=self.admin_user)   # ✅
        response = self.api_client.post(
            f'/api/orders/penalties/{self.penalty.id}/waive/',
            {'note': 'Waived due to client error'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.penalty.refresh_from_db()
        self.assertEqual(self.penalty.status, DeliveryPenalty.Status.WAIVED)

    def test_non_admin_cannot_apply_penalty(self):
        self.api_client.force_authenticate(user=self.editor_user)  # ✅
        response = self.api_client.post(
            f'/api/orders/penalties/{self.penalty.id}/apply/',
            {'note': 'Trying to apply'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_run_sla_check(self):
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post('/api/orders/penalties/check-all/')  # ✅ dash
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('penalties_created', response.data)


