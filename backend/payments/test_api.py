from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from payments import services
from payments.models import Wallet, WithdrawRequest


User = get_user_model()


def response_items(response):
    """
    Supports both paginated and non-paginated DRF responses.
    """
    data = response.data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


class PaymentAPITests(APITestCase):
    def create_user(self, username, role=None, is_staff=False):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )

        update_fields = []

        if role and any(field.name == "role" for field in User._meta.fields):
            user.role = role
            update_fields.append("role")

        if is_staff:
            user.is_staff = True
            update_fields.append("is_staff")

        if update_fields:
            user.save(update_fields=update_fields)

        return user

    def setUp(self):
        self.admin_user = self.create_user(
            "admin-user",
            role="admin",
            is_staff=True,
        )
        self.client_user = self.create_user(
            "client-user",
            role="client",
        )
        self.editor_user = self.create_user(
            "editor-user",
            role="editor",
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_my_wallet_requires_authentication(self):
        url = reverse("wallet-my-wallet")

        response = self.client.get(url)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_authenticated_user_can_get_my_wallet(self):
        self.authenticate(self.client_user)

        url = reverse("wallet-my-wallet")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_username"], self.client_user.username)
        self.assertEqual(Decimal(response.data["balance"]), Decimal("0"))
        self.assertEqual(Decimal(response.data["frozen_balance"]), Decimal("0"))
        self.assertEqual(Decimal(response.data["withdrawable_balance"]), Decimal("0"))

        self.assertTrue(Wallet.objects.filter(user=self.client_user).exists())

    def test_admin_can_deposit_to_user_wallet(self):
        self.authenticate(self.admin_user)

        url = reverse("wallet-admin-deposit")
        response = self.client.post(
            url,
            {
                "user_id": self.client_user.id,
                "amount": "75000",
                "description": "API test deposit",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        wallet = Wallet.objects.get(user=self.client_user)
        self.assertEqual(wallet.balance, Decimal("75000"))
        self.assertEqual(wallet.frozen_balance, Decimal("0"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("0"))

        self.assertEqual(response.data["tx_type"], "deposit")
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(Decimal(response.data["amount"]), Decimal("75000"))

    def test_non_admin_cannot_deposit_to_user_wallet(self):
        self.authenticate(self.client_user)

        url = reverse("wallet-admin-deposit")
        response = self.client.post(
            url,
            {
                "user_id": self.client_user.id,
                "amount": "75000",
                "description": "Forbidden deposit",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Wallet.objects.filter(user=self.client_user).exists())

    def test_admin_can_list_wallets(self):
        services.admin_deposit(
            user=self.client_user,
            amount=Decimal("50000"),
            admin_user=self.admin_user,
            description="Initial deposit",
        )

        self.authenticate(self.admin_user)

        url = reverse("wallet-admin-list-wallets")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        items = response_items(response)
        usernames = [item["user_username"] for item in items]

        self.assertIn(self.client_user.username, usernames)

    def test_editor_can_create_withdraw_request(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        self.authenticate(self.editor_user)

        url = reverse("withdraw-create-request")
        response = self.client.post(
            url,
            {
                "amount": "50000",
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Editor User",
                "editor_note": "Please process",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], WithdrawRequest.Status.PENDING)
        self.assertEqual(Decimal(response.data["amount"]), Decimal("50000"))

        wr = WithdrawRequest.objects.get(editor=self.editor_user)
        self.assertEqual(wr.amount, Decimal("50000"))
        self.assertEqual(wr.status, WithdrawRequest.Status.PENDING)

        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal("200000"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("200000"))

    def test_non_editor_cannot_create_withdraw_request(self):
        self.authenticate(self.client_user)

        url = reverse("withdraw-create-request")
        response = self.client.post(
            url,
            {
                "amount": "50000",
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Client User",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_list_own_withdraw_requests(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Editor User",
            },
        )

        self.authenticate(self.editor_user)

        url = reverse("withdraw-my-requests")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        items = response_items(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], WithdrawRequest.Status.PENDING)
        self.assertEqual(Decimal(items[0]["amount"]), Decimal("50000"))

    def test_admin_can_approve_withdraw_request(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        wr = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Editor User",
            },
        )

        self.authenticate(self.admin_user)

        url = reverse("withdraw-approve", args=[wr.id])
        response = self.client.post(
            url,
            {"admin_note": "Approved by API test"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], WithdrawRequest.Status.APPROVED)

        wr.refresh_from_db()
        wallet.refresh_from_db()

        self.assertEqual(wr.status, WithdrawRequest.Status.APPROVED)
        self.assertEqual(wr.reviewed_by, self.admin_user)
        self.assertIsNotNone(wr.reviewed_at)

        self.assertEqual(wallet.balance, Decimal("150000"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("150000"))

    def test_admin_can_mark_approved_withdraw_request_as_paid(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        wr = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Editor User",
            },
        )

        services.approve_withdrawal(wr, admin_user=self.admin_user)
        wr.refresh_from_db()

        self.authenticate(self.admin_user)

        url = reverse("withdraw-mark-paid", args=[wr.id])
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], WithdrawRequest.Status.PAID)

        wr.refresh_from_db()

        self.assertEqual(wr.status, WithdrawRequest.Status.PAID)
        self.assertIsNotNone(wr.paid_at)
        self.assertIn(self.admin_user.username, wr.admin_note)

    def test_admin_can_reject_pending_withdraw_request(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        wr = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Editor User",
            },
        )

        self.authenticate(self.admin_user)

        url = reverse("withdraw-reject", args=[wr.id])
        response = self.client.post(
            url,
            {"admin_note": "Rejected by API test"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], WithdrawRequest.Status.REJECTED)

        wr.refresh_from_db()
        wallet.refresh_from_db()

        self.assertEqual(wr.status, WithdrawRequest.Status.REJECTED)
        self.assertEqual(wr.admin_note, "Rejected by API test")

        # Reject should not deduct wallet balance.
        self.assertEqual(wallet.balance, Decimal("200000"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("200000"))

    def test_non_admin_cannot_approve_withdraw_request(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        wr = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789012345678901234",
                "account_holder_name": "Editor User",
            },
        )

        self.authenticate(self.client_user)

        url = reverse("withdraw-approve", args=[wr.id])
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        wr.refresh_from_db()
        self.assertEqual(wr.status, WithdrawRequest.Status.PENDING)