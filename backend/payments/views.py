from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services as payment_services
from . import gateway_zarinpal as zarinpal
from .models import PaymentRequest, Transaction, Wallet, WithdrawRequest
from .serializers import (
    AdminDepositSerializer,
    CreateWithdrawSerializer,
    InitiatePaymentSerializer,
    PaymentRequestSerializer,
    TransactionSerializer,
    WalletSerializer,
    WithdrawRequestSerializer,
    WithdrawReviewSerializer,
)

User = get_user_model()

STAFF_ROLES = {"admin", "supervisor", "support"}


def is_staff(user) -> bool:
    return user.role in STAFF_ROLES or user.is_staff


class WalletViewSet(viewsets.GenericViewSet):
    """
    کیف‌پول کاربر + تاریخچه تراکنش‌ها
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def my_wallet(self, request):
        """موجودی کیف‌پول من"""
        wallet = payment_services.get_or_create_wallet(request.user)
        return Response(WalletSerializer(wallet).data)

    @action(detail=False, methods=["get"], url_path="transactions")
    def my_transactions(self, request):
        """تاریخچه تراکنش‌های من"""
        wallet = payment_services.get_or_create_wallet(request.user)
        qs = wallet.transactions.order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(TransactionSerializer(page, many=True).data)
        return Response(TransactionSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="deposit/zarinpal")
    def initiate_zarinpal(self, request):
        """شروع پرداخت آنلاین با زرین‌پال"""
        ser = InitiatePaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        order = None
        if d.get("order_id"):
            from orders.models import Order
            try:
                order = Order.objects.get(id=d["order_id"], client=request.user)
            except Order.DoesNotExist:
                raise ValidationError({"order_id": "سفارش یافت نشد."})

        try:
            result = zarinpal.create_payment(
                user=request.user,
                amount=d["amount"],
                callback_url=d["callback_url"],
                description=d.get("description", "شارژ کیف‌پول"),
                order=order,
            )
        except ValueError as e:
            raise ValidationError({"detail": str(e)})

        return Response({
            "payment_url": result["payment_url"],
            "payment_request_id": result["payment_request"].id,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="deposit/zarinpal/callback")
    def zarinpal_callback(self, request):
        """callback زرین‌پال پس از پرداخت"""
        authority = request.query_params.get("Authority", "")
        status_param = request.query_params.get("Status", "")

        if not authority:
            return Response({"detail": "پارامتر Authority وجود ندارد."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with db_transaction.atomic():
                pr = zarinpal.verify_payment(authority=authority, status_param=status_param)
            return Response({
                "detail": "پرداخت موفق بود.",
                "ref_id": pr.ref_id,
                "amount": pr.amount,
            })
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ─── ادمین ────────────────────────────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="admin/deposit")
    def admin_deposit(self, request):
        """شارژ دستی کیف‌پول توسط ادمین"""
        if not is_staff(request.user):
            raise PermissionDenied("فقط ادمین می‌تواند شارژ دستی انجام دهد.")
        ser = AdminDepositSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        try:
            target_user = User.objects.get(id=d["user_id"])
        except User.DoesNotExist:
            raise ValidationError({"user_id": "کاربر یافت نشد."})

        tx = payment_services.admin_deposit(
            user=target_user,
            amount=d["amount"],
            admin_user=request.user,
            description=d.get("description", ""),
        )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="admin/wallets")
    def list_wallets(self, request):
        """لیست همه کیف‌پول‌ها — فقط ادمین"""
        if not is_staff(request.user):
            raise PermissionDenied()
        qs = Wallet.objects.select_related("user").order_by("-balance")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(WalletSerializer(page, many=True).data)
        return Response(WalletSerializer(qs, many=True).data)


class WithdrawViewSet(viewsets.GenericViewSet):
    """
    درخواست برداشت ادیتور
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="request")
    def create_request(self, request):
        """ادیتور درخواست برداشت ثبت می‌کند"""
        if request.user.role != "editor":
            raise PermissionDenied("فقط ادیتورها می‌توانند درخواست برداشت ثبت کنند.")

        ser = CreateWithdrawSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        try:
            wr = payment_services.request_withdrawal(
                editor=request.user,
                amount=d["amount"],
                bank_info={
                    "bank_name": d["bank_name"],
                    "card_number": d["card_number"],
                    "iban": d.get("iban", ""),
                    "account_holder_name": d["account_holder_name"],
                    "editor_note": d.get("editor_note", ""),
                },
            )
        except Exception as e:
            raise ValidationError({"detail": str(e)})

        return Response(WithdrawRequestSerializer(wr).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="my-requests")
    def my_requests(self, request):
        """لیست درخواست‌های برداشت خودم"""
        qs = WithdrawRequest.objects.filter(editor=request.user).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(WithdrawRequestSerializer(page, many=True).data)
        return Response(WithdrawRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """ادمین تأیید می‌کند"""
        if not is_staff(request.user):
            raise PermissionDenied()
        wr = self._get_wr(pk)
        ser = WithdrawReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            payment_services.approve_withdrawal(wr, admin_user=request.user)
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        return Response(WithdrawRequestSerializer(wr).data)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        """ادمین تأیید می‌کند که پول واریز شد"""
        if not is_staff(request.user):
            raise PermissionDenied()
        wr = self._get_wr(pk)
        try:
            payment_services.mark_withdrawal_paid(wr, admin_user=request.user)
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        return Response(WithdrawRequestSerializer(wr).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """ادمین رد می‌کند"""
        if not is_staff(request.user):
            raise PermissionDenied()
        wr = self._get_wr(pk)
        ser = WithdrawReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            payment_services.reject_withdrawal(
                wr,
                admin_user=request.user,
                note=ser.validated_data.get("admin_note", ""),
            )
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        return Response(WithdrawRequestSerializer(wr).data)

    @action(detail=False, methods=["get"], url_path="admin/all")
    def list_all(self, request):
        """ادمین همه درخواست‌ها را می‌بیند"""
        if not is_staff(request.user):
            raise PermissionDenied()
        qs = WithdrawRequest.objects.select_related("editor").order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(WithdrawRequestSerializer(page, many=True).data)
        return Response(WithdrawRequestSerializer(qs, many=True).data)

    def _get_wr(self, pk):
        try:
            return WithdrawRequest.objects.get(pk=pk)
        except WithdrawRequest.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("درخواست برداشت یافت نشد.")
