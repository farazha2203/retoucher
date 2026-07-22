"""
payments/settlement_views.py
پنل ادمین: مدیریت settlement_pending سفارش‌ها
"""
from decimal import Decimal

from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .permissions import IsAdmin
from .models import SiteCommissionSetting


# ─── Serializers ──────────────────────────────────────────────────────────────

class SettlementOrderSerializer(serializers.Serializer):
    """نمایش سفارش در صف settlement"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.SerializerMethodField()
    client_username = serializers.CharField()
    client_email = serializers.CharField()
    editor_username = serializers.CharField(allow_null=True)
    editor_email = serializers.CharField(allow_null=True)
    agreed_price = serializers.DecimalField(max_digits=14, decimal_places=0)
    commission_amount = serializers.DecimalField(max_digits=14, decimal_places=0)
    editor_earning = serializers.DecimalField(max_digits=14, decimal_places=0)
    escrow_held = serializers.BooleanField()
    payment_settled = serializers.BooleanField()
    settlement_started_at = serializers.DateTimeField(allow_null=True)
    paid_at = serializers.DateTimeField(allow_null=True)
    closed_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    days_in_settlement = serializers.SerializerMethodField()

    STATUS_LABELS = {
        "draft": "پیش‌نویس",
        "submitted": "ثبت شده",
        "in_review": "در حال بررسی",
        "assigned": "اختصاص یافته",
        "in_progress": "در حال انجام",
        "delivered": "تحویل داده شده",
        "client_review": "بررسی مشتری",
        "revision_required": "نیاز به اصلاح",
        "client_revision_requested": "درخواست اصلاح مشتری",
        "completed": "تکمیل شده",
        "settlement_pending": "در انتظار تسویه",
        "paid": "پرداخت شده",
        "closed": "بسته شده",
        "cancelled": "لغو شده",
    }

    def get_status_display(self, obj):
        if hasattr(obj, 'get_status_display'):
            return self.STATUS_LABELS.get(obj.status, obj.status)
        return self.STATUS_LABELS.get(obj.get("status", ""), "")

    def get_days_in_settlement(self, obj):
        started = obj.settlement_started_at if hasattr(obj, 'settlement_started_at') else obj.get("settlement_started_at")
        if started:
            return (timezone.now() - started).days
        return None

    def to_representation(self, instance):
        # پشتیبانی از هر دو حالت Model و dict
        if hasattr(instance, '__dict__'):
            return {
                "id": instance.id,
                "title": instance.title,
                "status": instance.status,
                "status_display": self.STATUS_LABELS.get(instance.status, instance.status),
                "client_username": instance.client.username,
                "client_email": instance.client.email,
                "editor_username": instance.editor.username if instance.editor else None,
                "editor_email": instance.editor.email if instance.editor else None,
                "agreed_price": instance.agreed_price,
                "commission_amount": instance.commission_amount,
                "editor_earning": instance.editor_earning,
                "escrow_held": instance.escrow_held,
                "payment_settled": instance.payment_settled,
                "settlement_started_at": instance.settlement_started_at,
                "paid_at": instance.paid_at,
                "closed_at": instance.closed_at,
                "created_at": instance.created_at,
                "days_in_settlement": (
                    (timezone.now() - instance.settlement_started_at).days
                    if instance.settlement_started_at else None
                ),
            }
        return super().to_representation(instance)


class SetAgreedPriceSerializer(serializers.Serializer):
    agreed_price = serializers.DecimalField(
        max_digits=14, decimal_places=0,
        min_value=Decimal("1000"),
    )
    note = serializers.CharField(max_length=500, required=False, default="")


class SettlementActionSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=500, required=False, default="")


# ─── View ─────────────────────────────────────────────────────────────────────

class SettlementAdminViewSet(GenericViewSet):
    """
    پنل ادمین: مدیریت کامل settlement
    """
    permission_classes = [IsAdmin]

    def _get_order(self, pk):
        from orders.models import Order
        try:
            return Order.objects.select_related("client", "editor").get(pk=pk)
        except Order.DoesNotExist:
            raise NotFound("سفارش یافت نشد.")

    @action(detail=False, methods=["get"], url_path="pending")
    def list_pending(self, request):
        """
        لیست سفارش‌های در انتظار تسویه
        قابل فیلتر بر اساس تاریخ و مبلغ
        """
        from orders.models import Order
        qs = Order.objects.filter(
            status=Order.Status.SETTLEMENT_PENDING
        ).select_related("client", "editor").order_by("settlement_started_at")

        # فیلترها
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        min_amount = request.query_params.get("min_amount")
        max_amount = request.query_params.get("max_amount")
        search = request.query_params.get("search", "").strip()

        if date_from:
            qs = qs.filter(settlement_started_at__gte=date_from)
        if date_to:
            qs = qs.filter(settlement_started_at__lte=date_to)
        if min_amount:
            qs = qs.filter(agreed_price__gte=min_amount)
        if max_amount:
            qs = qs.filter(agreed_price__lte=max_amount)
        if search:
            qs = qs.filter(
                Q(client__username__icontains=search) |
                Q(editor__username__icontains=search) |
                Q(title__icontains=search)
            )

        summary = qs.aggregate(
            count=Count("id"),
            total_amount=Sum("agreed_price"),
        )

        page = self.paginate_queryset(qs)
        data = SettlementOrderSerializer(page if page is not None else qs, many=True).data

        response_data = {
            "summary": {
                "count": summary["count"] or 0,
                "total_amount": summary["total_amount"] or 0,
            },
            "results": data,
        }

        if page is not None:
            return self.get_paginated_response(response_data)
        return Response(response_data)

    @action(detail=False, methods=["get"], url_path="all")
    def list_all(self, request):
        """همه سفارش‌ها با فیلتر وضعیت"""
        from orders.models import Order
        qs = Order.objects.select_related("client", "editor").order_by("-updated_at")

        order_status = request.query_params.get("status")
        payment_settled = request.query_params.get("payment_settled")
        search = request.query_params.get("search", "").strip()

        if order_status:
            qs = qs.filter(status=order_status)
        if payment_settled is not None:
            qs = qs.filter(payment_settled=payment_settled.lower() == "true")
        if search:
            qs = qs.filter(
                Q(client__username__icontains=search) |
                Q(editor__username__icontains=search) |
                Q(title__icontains=search)
            )

        page = self.paginate_queryset(qs)
        data = SettlementOrderSerializer(page if page is not None else qs, many=True).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    @action(detail=True, methods=["get"], url_path="detail")
    def order_detail(self, request, pk=None):
        """جزئیات یک سفارش برای پنل settlement"""
        order = self._get_order(pk)
        commission = SiteCommissionSetting.get_active()
        data = SettlementOrderSerializer(order).data

        # محاسبه پیش‌نمایش کمیسیون اگر هنوز تسویه نشده
        if not order.payment_settled and order.agreed_price and commission:
            comm, earning = commission.calculate(order.agreed_price)
            data["preview_commission"] = comm
            data["preview_editor_earning"] = earning
            data["active_commission_percent"] = commission.commission_percent
        return Response(data)

    @action(detail=True, methods=["post"], url_path="set-price")
    def set_agreed_price(self, request, pk=None):
        """
        ادمین مبلغ نهایی سفارش را تنظیم می‌کند
        فقط اگر هنوز escrow_held=False باشد
        """
        order = self._get_order(pk)

        if order.payment_settled:
            raise ValidationError({"detail": "سفارش قبلاً تسویه شده — قابل ویرایش نیست."})

        ser = SetAgreedPriceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        order.agreed_price = d["agreed_price"]
        order.save(update_fields=["agreed_price", "updated_at"])

        from orders.models import OrderActivityLog
        OrderActivityLog.objects.create(
            order=order,
            actor=request.user,
            activity_type=OrderActivityLog.ActivityType.SETTLEMENT_STARTED,
            message=f"مبلغ سفارش توسط ادمین به {d['agreed_price']:,} تومان تنظیم شد.",
            metadata={"agreed_price": str(d["agreed_price"]), "note": d.get("note", "")},
        )

        return Response(SettlementOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="settle")
    def settle(self, request, pk=None):
        """
        تسویه نهایی سفارش:
        - کسر از کیف‌پول مشتری
        - کمیسیون سایت
        - واریز به ادیتور
        - تغییر وضعیت به PAID
        """
        from orders.models import Order, OrderActivityLog
        from payments.order_hooks import on_order_settlement
        from django.db import transaction as db_tx

        order = self._get_order(pk)

        if order.payment_settled:
            raise ValidationError({"detail": "این سفارش قبلاً تسویه شده است."})

        if order.status not in (Order.Status.SETTLEMENT_PENDING, Order.Status.COMPLETED):
            raise ValidationError({
                "detail": f"وضعیت سفارش '{order.status}' قابل تسویه نیست. باید completed یا settlement_pending باشد."
            })

        if not order.agreed_price or order.agreed_price <= 0:
            raise ValidationError({"detail": "ابتدا مبلغ سفارش (agreed_price) را تنظیم کنید."})

        if not order.editor:
            raise ValidationError({"detail": "سفارش ادیتور ندارد."})

        note = request.data.get("note", "").strip()

        try:
            with db_tx.atomic():
                result = on_order_settlement(order, admin_user=request.user)
                order.refresh_from_db()

                OrderActivityLog.objects.create(
                    order=order,
                    actor=request.user,
                    activity_type=OrderActivityLog.ActivityType.PAYMENT_RECORDED,
                    message="تسویه مالی انجام شد.",
                    metadata={
                        "note": note,
                        "agreed_price": str(order.agreed_price),
                        "commission": str(result["commission"]),
                        "editor_earning": str(result["editor_earning"]),
                        "client_tx_id": result["client_tx"].id,
                        "editor_tx_id": result["editor_tx"].id,
                    },
                )
        except ValueError as e:
            raise ValidationError({"detail": str(e)})
        except Exception as e:
            raise ValidationError({"detail": f"خطا در تسویه: {str(e)}"})

        order.refresh_from_db()
        return Response({
            "order": SettlementOrderSerializer(order).data,
            "settlement": {
                "agreed_price": str(order.agreed_price),
                "commission": str(result["commission"]),
                "editor_earning": str(result["editor_earning"]),
                "client_tx_id": result["client_tx"].id,
                "editor_tx_id": result["editor_tx"].id,
            },
        })

    @action(detail=False, methods=["get"], url_path="summary")
    def settlement_summary(self, request):
        """خلاصه آماری settlement برای داشبورد ادمین"""
        from orders.models import Order
        from payments.models import Transaction

        qs = Order.objects.all()

        pending_qs = qs.filter(status=Order.Status.SETTLEMENT_PENDING)
        paid_qs = qs.filter(status=Order.Status.PAID)
        settled_qs = qs.filter(payment_settled=True)

        pending_agg = pending_qs.aggregate(count=Count("id"), total=Sum("agreed_price"))
        paid_agg = paid_qs.aggregate(count=Count("id"), total=Sum("agreed_price"))
        settled_agg = settled_qs.aggregate(
            count=Count("id"),
            total_commission=Sum("commission_amount"),
            total_editor=Sum("editor_earning"),
        )

        # قدیمی‌ترین pending (بیش از X روز)
        old_pending = pending_qs.filter(
            settlement_started_at__lt=timezone.now() - timezone.timedelta(days=3)
        ).count()

        commission = SiteCommissionSetting.get_active()

        return Response({
            "pending": {
                "count": pending_agg["count"] or 0,
                "total_amount": pending_agg["total"] or 0,
                "older_than_3_days": old_pending,
            },
            "paid": {
                "count": paid_agg["count"] or 0,
                "total_amount": paid_agg["total"] or 0,
            },
            "settled": {
                "count": settled_agg["count"] or 0,
                "total_commission_earned": settled_agg["total_commission"] or 0,
                "total_editor_paid": settled_agg["total_editor"] or 0,
            },
            "active_commission_percent": str(commission.commission_percent) if commission else "10.00",
        })
