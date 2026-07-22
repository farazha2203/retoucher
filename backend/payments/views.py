"""
payments/views.py — نسخه کامل و امن
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from . import gateway_zarinpal as zarinpal
from . import services as payment_services
from . import reports
from .filters import PaymentRequestFilter, TransactionFilter, WalletFilter, WithdrawRequestFilter
from .models import PaymentRequest, SiteCommissionSetting, Transaction, Wallet, WithdrawRequest
from .permissions import IsAdmin, IsEditor, IsOwnerOrAdmin
from .serializers import (
    AdminDepositSerializer,
    CommissionSettingSerializer,
    CreateCommissionSettingSerializer,
    CreateWithdrawSerializer,
    InitiatePaymentSerializer,
    InvoiceSerializer,
    PaymentRequestPublicSerializer,
    PaymentRequestSerializer,
    PaymentSummarySerializer,
    TransactionSerializer,
    WalletSerializer,
    WithdrawRequestSerializer,
    WithdrawReviewSerializer,
)

User = get_user_model()


class PaymentRateThrottle(UserRateThrottle):
    rate = "10/minute"


# ─── Wallet ───────────────────────────────────────────────────────────────────

class WalletViewSet(viewsets.GenericViewSet):
    """
    کیف‌پول — کاربر موجودی و تاریخچه خود را می‌بیند
    ادمین همه کیف‌پول‌ها را مدیریت می‌کند
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = WalletFilter
    ordering_fields = ["balance", "updated_at"]
    ordering = ["-balance"]

    # ── کاربر: کیف‌پول خودم ──────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="me")
    def my_wallet(self, request):
        """موجودی کیف‌پول من"""
        wallet = payment_services.get_or_create_wallet(request.user)
        return Response(WalletSerializer(wallet).data)

    @action(detail=False, methods=["get"], url_path="me/transactions")
    def my_transactions(self, request):
        """تاریخچه تراکنش‌های من با فیلتر"""
        wallet = payment_services.get_or_create_wallet(request.user)
        qs = wallet.transactions.select_related("order").order_by("-created_at")

        # فیلتر دستی
        tx_type = request.query_params.get("tx_type")
        tx_status = request.query_params.get("status")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if tx_type:
            qs = qs.filter(tx_type=tx_type)
        if tx_status:
            qs = qs.filter(status=tx_status)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(TransactionSerializer(page, many=True).data)
        return Response(TransactionSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="me/payments")
    def my_payments(self, request):
        """تاریخچه پرداخت‌های آنلاین من"""
        qs = PaymentRequest.objects.filter(user=request.user).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PaymentRequestPublicSerializer(page, many=True).data)
        return Response(PaymentRequestPublicSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="me/payments/(?P<payment_id>[0-9]+)")
    def my_payment_detail(self, request, payment_id=None):
        """جزئیات یک پرداخت آنلاین خودم"""
        try:
            pr = PaymentRequest.objects.get(id=payment_id, user=request.user)
        except PaymentRequest.DoesNotExist:
            raise NotFound("پرداخت یافت نشد.")
        return Response(PaymentRequestPublicSerializer(pr).data)

    @action(detail=False, methods=["get"], url_path="me/invoice")
    def my_invoice(self, request):
        """صورت‌حساب من"""
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        data = reports.get_user_invoice(
            user=request.user,
            date_from=date_from,
            date_to=date_to,
        )
        return Response(InvoiceSerializer(data).data)

    # ── پرداخت آنلاین (زرین‌پال) ─────────────────────────────────────────────

    @action(
        detail=False, methods=["post"],
        url_path="deposit/zarinpal",
        throttle_classes=[PaymentRateThrottle],
    )
    def initiate_zarinpal(self, request):
        """شروع پرداخت آنلاین"""
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
        """callback زرین‌پال"""
        authority = request.query_params.get("Authority", "")
        status_param = request.query_params.get("Status", "")

        if not authority:
            return Response(
                {"detail": "پارامتر Authority وجود ندارد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with db_transaction.atomic():
                pr = zarinpal.verify_payment(authority=authority, status_param=status_param)
            return Response({
                "success": True,
                "ref_id": pr.ref_id,
                "amount": pr.amount,
                "message": "پرداخت با موفقیت انجام شد.",
            })
        except ValueError as e:
            return Response({"success": False, "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="deposit/zarinpal/retry/(?P<payment_id>[0-9]+)")
    def retry_payment(self, request, payment_id=None):
        """
        بررسی مجدد وضعیت یک پرداخت pending
        اگر هنوز باز باشد می‌توان دوباره به درگاه هدایت کرد
        """
        try:
            pr = PaymentRequest.objects.get(id=payment_id, user=request.user)
        except PaymentRequest.DoesNotExist:
            raise NotFound("پرداخت یافت نشد.")

        if pr.status == PaymentRequest.Status.SUCCESS:
            return Response({"detail": "این پرداخت قبلاً تأیید شده است.", "ref_id": pr.ref_id})

        if pr.status not in (PaymentRequest.Status.REDIRECTED, PaymentRequest.Status.CREATED):
            return Response(
                {"detail": f"وضعیت پرداخت '{pr.get_status_display()}' قابل بررسی مجدد نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pr.authority:
            return Response({
                "payment_url": zarinpal._startpay_url(pr.authority),
                "payment_request_id": pr.id,
                "message": "لینک پرداخت مجدداً ارسال شد.",
            })

        return Response(
            {"detail": "این پرداخت فاقد Authority است. لطفاً پرداخت جدید ایجاد کنید."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── ادمین ────────────────────────────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="admin/deposit", permission_classes=[IsAdmin])
    def admin_deposit(self, request):
        """شارژ دستی کیف‌پول توسط ادمین"""
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

    @action(detail=False, methods=["get"], url_path="admin/wallets", permission_classes=[IsAdmin])
    def admin_list_wallets(self, request):
        """لیست همه کیف‌پول‌ها"""
        qs = Wallet.objects.select_related("user").order_by("-balance")
        filterset = WalletFilter(request.query_params, queryset=qs)
        qs = filterset.qs
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(WalletSerializer(page, many=True).data)
        return Response(WalletSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="admin/wallets/(?P<user_id>[0-9]+)", permission_classes=[IsAdmin])
    def admin_wallet_detail(self, request, user_id=None):
        """جزئیات کیف‌پول یک کاربر"""
        try:
            wallet = Wallet.objects.select_related("user").get(user_id=user_id)
        except Wallet.DoesNotExist:
            raise NotFound("کیف‌پول یافت نشد.")
        return Response(WalletSerializer(wallet).data)

    @action(detail=False, methods=["get"], url_path="admin/transactions", permission_classes=[IsAdmin])
    def admin_list_transactions(self, request):
        """همه تراکنش‌ها با فیلتر کامل"""
        qs = Transaction.objects.select_related("wallet__user", "order").order_by("-created_at")
        filterset = TransactionFilter(request.query_params, queryset=qs)
        qs = filterset.qs
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(TransactionSerializer(page, many=True).data)
        return Response(TransactionSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="admin/payments", permission_classes=[IsAdmin])
    def admin_list_payments(self, request):
        """همه پرداخت‌های آنلاین"""
        qs = PaymentRequest.objects.select_related("user", "order").order_by("-created_at")
        filterset = PaymentRequestFilter(request.query_params, queryset=qs)
        qs = filterset.qs
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PaymentRequestSerializer(page, many=True).data)
        return Response(PaymentRequestSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="admin/payments/pending", permission_classes=[IsAdmin])
    def admin_pending_payments(self, request):
        """پرداخت‌های در انتظار — نیاز به پیگیری"""
        qs = reports.get_pending_payments()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PaymentRequestSerializer(page, many=True).data)
        return Response(PaymentRequestSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="admin/summary", permission_classes=[IsAdmin])
    def admin_summary(self, request):
        """داشبورد مالی ادمین"""
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        data = reports.get_admin_summary(date_from=date_from, date_to=date_to)
        return Response(PaymentSummarySerializer(data).data)

    @action(detail=False, methods=["get"], url_path="admin/status-breakdown", permission_classes=[IsAdmin])
    def admin_status_breakdown(self, request):
        """تفکیک وضعیت پرداخت‌ها"""
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        data = reports.get_payment_status_breakdown(date_from=date_from, date_to=date_to)
        return Response(data)

    @action(detail=False, methods=["get"], url_path="admin/invoice/(?P<user_id>[0-9]+)", permission_classes=[IsAdmin])
    def admin_user_invoice(self, request, user_id=None):
        """صورت‌حساب یک کاربر — برای ادمین"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("کاربر یافت نشد.")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        data = reports.get_user_invoice(user=user, date_from=date_from, date_to=date_to)
        return Response(InvoiceSerializer(data).data)

    # ── تنظیمات کمیسیون ──────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="admin/commission", permission_classes=[IsAdmin])
    def get_commission(self, request):
        """تنظیمات کمیسیون فعال"""
        setting = SiteCommissionSetting.get_active()
        if not setting:
            return Response({"detail": "تنظیمات کمیسیونی وجود ندارد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CommissionSettingSerializer(setting).data)

    @action(detail=False, methods=["get"], url_path="admin/commission/history", permission_classes=[IsAdmin])
    def commission_history(self, request):
        """تاریخچه تغییرات کمیسیون"""
        qs = SiteCommissionSetting.objects.select_related("created_by").order_by("-created_at")
        return Response(CommissionSettingSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="admin/commission", permission_classes=[IsAdmin])
    def set_commission(self, request):
        """تغییر نرخ کمیسیون — قبلی غیرفعال می‌شود"""
        ser = CreateCommissionSettingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        with db_transaction.atomic():
            SiteCommissionSetting.objects.filter(is_active=True).update(is_active=False)
            setting = SiteCommissionSetting.objects.create(
                commission_percent=d["commission_percent"],
                min_commission=d.get("min_commission", Decimal("0")),
                note=d.get("note", ""),
                is_active=True,
                created_by=request.user,
            )
        return Response(CommissionSettingSerializer(setting).data, status=status.HTTP_201_CREATED)


# ─── WithdrawRequest ──────────────────────────────────────────────────────────

class WithdrawViewSet(viewsets.GenericViewSet):
    """
    درخواست برداشت ادیتور
    """
    permission_classes = [IsAuthenticated]

    @action(
        detail=False, methods=["post"],
        url_path="request",
        permission_classes=[IsEditor],
        throttle_classes=[PaymentRateThrottle],
    )
    def create_request(self, request):
        """ادیتور درخواست برداشت ثبت می‌کند"""
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

    @action(detail=False, methods=["get"], url_path="my-requests", permission_classes=[IsEditor])
    def my_requests(self, request):
        """لیست درخواست‌های برداشت خودم"""
        qs = WithdrawRequest.objects.filter(editor=request.user).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(WithdrawRequestSerializer(page, many=True).data)
        return Response(WithdrawRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="detail", permission_classes=[IsEditor])
    def my_request_detail(self, request, pk=None):
        """جزئیات یک درخواست برداشت خودم"""
        wr = self._get_my_wr(pk, request.user)
        return Response(WithdrawRequestSerializer(wr).data)

    # ── ادمین: مدیریت برداشت‌ها ──────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="admin/all", permission_classes=[IsAdmin])
    def admin_list_all(self, request):
        """ادمین همه درخواست‌ها را می‌بیند"""
        qs = WithdrawRequest.objects.select_related("editor", "reviewed_by").order_by("-created_at")
        filterset = WithdrawRequestFilter(request.query_params, queryset=qs)
        qs = filterset.qs
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(WithdrawRequestSerializer(page, many=True).data)
        return Response(WithdrawRequestSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="admin/pending", permission_classes=[IsAdmin])
    def admin_pending(self, request):
        """فقط درخواست‌های در انتظار"""
        qs = WithdrawRequest.objects.filter(
            status=WithdrawRequest.Status.PENDING
        ).select_related("editor").order_by("created_at")
        return Response(WithdrawRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        """تأیید درخواست برداشت"""
        wr = self._get_wr(pk)
        ser = WithdrawReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if ser.validated_data.get("admin_note"):
            wr.admin_note = ser.validated_data["admin_note"]
            wr.save(update_fields=["admin_note"])
        try:
            payment_services.approve_withdrawal(wr, admin_user=request.user)
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        wr.refresh_from_db()
        return Response(WithdrawRequestSerializer(wr).data)

    @action(detail=True, methods=["post"], url_path="mark-paid", permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        """تأیید پرداخت — پول واریز شد"""
        wr = self._get_wr(pk)
        try:
            payment_services.mark_withdrawal_paid(wr, admin_user=request.user)
        except Exception as e:
            raise ValidationError({"detail": str(e)})
        wr.refresh_from_db()
        return Response(WithdrawRequestSerializer(wr).data)

    @action(detail=True, methods=["post"], url_path="reject", permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        """رد درخواست برداشت"""
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
        wr.refresh_from_db()
        return Response(WithdrawRequestSerializer(wr).data)

    def _get_wr(self, pk):
        try:
            return WithdrawRequest.objects.select_for_update().get(pk=pk)
        except WithdrawRequest.DoesNotExist:
            raise NotFound("درخواست برداشت یافت نشد.")

    def _get_my_wr(self, pk, user):
        try:
            return WithdrawRequest.objects.get(pk=pk, editor=user)
        except WithdrawRequest.DoesNotExist:
            raise NotFound("درخواست برداشت یافت نشد.")
