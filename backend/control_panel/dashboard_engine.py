from __future__ import annotations

from collections import OrderedDict
from decimal import Decimal

from django.apps import apps
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .access import (
    is_finance_admin,
    is_order_staff,
    visible_orders,
    visible_projects,
    visible_refunds,
    visible_transactions,
    visible_wallets,
)


ACTIVE_ORDER_STATUSES = {
    "submitted",
    "in_review",
    "assigned",
    "in_progress",
    "delivered",
    "client_review",
    "revision_required",
    "client_revision_requested",
    "settlement_pending",
}

COMPLETED_ORDER_STATUSES = {"completed", "paid", "closed"}


def _model(label):
    try:
        return apps.get_model(label)
    except Exception:
        return None


def _sum(queryset, field):
    if queryset is None:
        return Decimal("0")
    return queryset.aggregate(total=Sum(field))["total"] or Decimal("0")


def _count(queryset):
    return queryset.count() if queryset is not None else 0


def _monthly_counts(queryset, field="created_at", months=8):
    if queryset is None:
        return [], []

    start = timezone.now() - timezone.timedelta(days=31 * months)
    rows = (
        queryset.filter(**{f"{field}__gte": start})
        .annotate(period=TruncMonth(field))
        .values("period")
        .annotate(total=Count("id"))
        .order_by("period")
    )
    labels = [
        row["period"].strftime("%Y-%m")
        for row in rows
        if row["period"] is not None
    ]
    values = [
        row["total"]
        for row in rows
        if row["period"] is not None
    ]
    return labels, values


def _status_series(queryset):
    if queryset is None:
        return [], []

    rows = list(
        queryset.values("status")
        .annotate(total=Count("id"))
        .order_by("-total", "status")
    )
    return (
        [row["status"] for row in rows],
        [row["total"] for row in rows],
    )


def _deadline_queryset(user, orders, projects):
    Deadline = _model("orders.WorkflowDeadline")
    if Deadline is None:
        return None

    queryset = Deadline.objects.select_related(
        "order",
        "project_request",
    )

    if is_order_staff(user):
        return queryset

    order_ids = orders.values_list("id", flat=True) if orders is not None else []
    project_ids = (
        projects.values_list("id", flat=True)
        if projects is not None else []
    )
    return queryset.filter(
        Q(order_id__in=order_ids)
        | Q(project_request_id__in=project_ids)
    )


def _notification_queryset(user):
    Notification = _model("notifications.Notification")
    if Notification is None:
        return None
    return Notification.objects.filter(recipient=user)


def _conversation_queryset(user):
    Conversation = _model("operations_hub.Conversation")
    if Conversation is None:
        return None

    if is_order_staff(user):
        return Conversation.objects.all()

    return Conversation.objects.filter(
        Q(participants=user)
        | Q(created_by=user)
        | Q(order__client=user)
        | Q(order__editor=user)
        | Q(project_request__client=user)
        | Q(project_request__target_editor__user=user)
    ).distinct()


def _common_context(user):
    Order = _model("orders.Order")
    Project = _model("projects.ProjectRequest")
    Wallet = _model("payments.Wallet")
    Transaction = _model("payments.Transaction")
    Refund = _model("payments.Refund")

    orders = (
        visible_orders(user, Order.objects.all())
        if Order is not None
        else None
    )
    projects = (
        visible_projects(user, Project.objects.all())
        if Project is not None
        else None
    )
    wallets = (
        visible_wallets(user, Wallet.objects.all())
        if Wallet is not None
        else None
    )
    transactions = (
        visible_transactions(user, Transaction.objects.all())
        if Transaction is not None
        else None
    )
    refunds = (
        visible_refunds(user, Refund.objects.all())
        if Refund is not None
        else None
    )
    deadlines = _deadline_queryset(user, orders, projects)
    notifications = _notification_queryset(user)
    conversations = _conversation_queryset(user)

    status_labels, status_values = _status_series(orders)
    month_labels, month_values = _monthly_counts(orders)

    active_orders = (
        orders.filter(status__in=ACTIVE_ORDER_STATUSES)
        if orders is not None
        else None
    )
    completed_orders = (
        orders.filter(status__in=COMPLETED_ORDER_STATUSES)
        if orders is not None
        else None
    )

    total_orders = _count(orders)
    completed_count = _count(completed_orders)

    return {
        "orders": orders,
        "projects": projects,
        "wallets": wallets,
        "transactions": transactions,
        "refunds": refunds,
        "deadlines": deadlines,
        "notifications": notifications,
        "conversations": conversations,
        "total_orders": total_orders,
        "active_orders_count": _count(active_orders),
        "completed_orders_count": completed_count,
        "completion_percent": round(
            (completed_count / total_orders) * 100,
            1,
        ) if total_orders else 0,
        "project_count": _count(projects),
        "wallet_balance": _sum(wallets, "balance"),
        "frozen_balance": _sum(wallets, "frozen_balance"),
        "withdrawable_balance": _sum(wallets, "withdrawable_balance"),
        "successful_volume": _sum(
            transactions.filter(status="success")
            if transactions is not None else None,
            "amount",
        ),
        "transaction_count": _count(transactions),
        "refund_count": _count(refunds),
        "unread_notifications": (
            notifications.filter(is_read=False).count()
            if notifications is not None else 0
        ),
        "conversation_count": _count(conversations),
        "active_deadlines": (
            deadlines.filter(status="active").count()
            if deadlines is not None else 0
        ),
        "overdue_deadlines": (
            deadlines.filter(
                status="active",
                due_at__lt=timezone.now(),
            ).count()
            if deadlines is not None else 0
        ),
        "status_labels": status_labels,
        "status_values": status_values,
        "month_labels": month_labels,
        "month_values": month_values,
        "recent_orders": list(
            orders.select_related("client", "editor")
            .order_by("-updated_at", "-id")[:8]
        ) if orders is not None else [],
        "recent_transactions": list(
            transactions.select_related("wallet__user", "order")
            .order_by("-created_at", "-id")[:8]
        ) if transactions is not None else [],
        "upcoming_deadlines": list(
            deadlines.filter(status="active")
            .order_by("due_at", "id")[:8]
        ) if deadlines is not None else [],
    }


def _client_dashboard(user, context):
    orders = context["orders"]
    refunds = context["refunds"]

    review_statuses = {
        "client_review",
        "client_revision_requested",
    }

    context.update({
        "dashboard_kind": "client",
        "page_title": "داشبورد مشتری",
        "hero_title": "مرکز پیگیری سفارش‌های شما",
        "hero_subtitle": (
            "وضعیت سفارش، پرداخت، فایل‌ها، اصلاحات و مهلت‌ها را "
            "در یک نمای یکپارچه دنبال کنید."
        ),
        "attention_count": (
            orders.filter(status__in=review_statuses).count()
            if orders is not None else 0
        ),
        "draft_count": (
            orders.filter(status="draft").count()
            if orders is not None else 0
        ),
        "escrow_orders": (
            orders.filter(escrow_held=True).count()
            if orders is not None else 0
        ),
        "pending_refunds": (
            refunds.filter(
                status__in=["requested", "under_review", "approved"]
            ).count()
            if refunds is not None else 0
        ),
        "primary_kpis": [
            {
                "title": "سفارش فعال",
                "value": context["active_orders_count"],
                "icon": "ri-loader-4-line",
                "color": "primary",
                "url_name": "control_panel:orders",
            },
            {
                "title": "منتظر اقدام شما",
                "value": (
                    orders.filter(status__in=review_statuses).count()
                    if orders is not None else 0
                ),
                "icon": "ri-user-follow-line",
                "color": "warning",
                "url_name": "control_panel:orders",
            },
            {
                "title": "موجودی کیف پول",
                "value": context["wallet_balance"],
                "suffix": " تومان",
                "icon": "ri-wallet-3-line",
                "color": "success",
                "url_name": "control_panel:finance",
                "is_money": True,
            },
            {
                "title": "وجه بلوکه‌شده",
                "value": context["frozen_balance"],
                "suffix": " تومان",
                "icon": "ri-lock-2-line",
                "color": "info",
                "url_name": "control_panel:finance",
                "is_money": True,
            },
        ],
    })


def _editor_dashboard(user, context):
    orders = context["orders"]
    transactions = context["transactions"]
    Withdraw = _model("payments.WithdrawRequest")
    profile = getattr(user, "editor_profile", None)

    earning_transactions = (
        transactions.filter(
            tx_type="editor_earning",
            status="success",
        )
        if transactions is not None else None
    )

    context.update({
        "dashboard_kind": "editor",
        "page_title": "داشبورد ادیتور",
        "hero_title": "مرکز اجرای پروژه‌ها و درآمد شما",
        "hero_subtitle": (
            "بار کاری، تحویل‌های نزدیک، اصلاحات، درآمد و ظرفیت کاری "
            "خود را مدیریت کنید."
        ),
        "editor_profile": profile,
        "assigned_count": (
            orders.filter(status="assigned").count()
            if orders is not None else 0
        ),
        "in_progress_count": (
            orders.filter(status="in_progress").count()
            if orders is not None else 0
        ),
        "revision_count": (
            orders.filter(
                status__in=[
                    "revision_required",
                    "client_revision_requested",
                ]
            ).count()
            if orders is not None else 0
        ),
        "delivery_due_count": (
            orders.filter(
                deadline__isnull=False,
                deadline__lte=timezone.now() + timezone.timedelta(hours=48),
                status__in=["assigned", "in_progress", "revision_required"],
            ).count()
            if orders is not None else 0
        ),
        "total_earnings": _sum(earning_transactions, "amount"),
        "pending_withdraws": (
            Withdraw.objects.filter(
                editor=user,
                status="pending",
            ).count()
            if Withdraw is not None else 0
        ),
        "primary_kpis": [
            {
                "title": "کار در حال انجام",
                "value": (
                    orders.filter(status="in_progress").count()
                    if orders is not None else 0
                ),
                "icon": "ri-brush-3-line",
                "color": "primary",
                "url_name": "control_panel:orders",
            },
            {
                "title": "نیازمند اصلاح",
                "value": (
                    orders.filter(
                        status__in=[
                            "revision_required",
                            "client_revision_requested",
                        ]
                    ).count()
                    if orders is not None else 0
                ),
                "icon": "ri-restart-line",
                "color": "warning",
                "url_name": "control_panel:orders",
            },
            {
                "title": "قابل برداشت",
                "value": context["withdrawable_balance"],
                "suffix": " تومان",
                "icon": "ri-bank-card-line",
                "color": "success",
                "url_name": "control_panel:finance",
                "is_money": True,
            },
            {
                "title": "امتیاز ادیتور",
                "value": getattr(profile, "rating_average", 0),
                "suffix": " از ۵",
                "icon": "ri-star-smile-line",
                "color": "info",
                "url_name": "control_panel:settings",
            },
        ],
    })


def _support_dashboard(user, context):
    Order = _model("orders.Order")
    Refund = _model("payments.Refund")
    Withdraw = _model("payments.WithdrawRequest")
    Dispute = _model("orders.Dispute")

    context.update({
        "dashboard_kind": "support",
        "page_title": "داشبورد پشتیبانی",
        "hero_title": "مرکز صف‌های عملیاتی و پیگیری",
        "hero_subtitle": (
            "سفارش‌های منتظر بررسی، اختلاف‌ها، استردادها، SLA و "
            "گفتگوهای نیازمند رسیدگی را مشاهده کنید."
        ),
        "review_queue": (
            Order.objects.filter(
                status__in=["submitted", "in_review"]
            ).count() if Order is not None else 0
        ),
        "open_disputes": (
            Dispute.objects.filter(
                status__in=["open", "under_review"]
            ).count() if Dispute is not None else 0
        ),
        "pending_refunds": (
            Refund.objects.filter(
                status__in=["requested", "under_review"]
            ).count() if Refund is not None else 0
        ),
        "pending_withdraws": (
            Withdraw.objects.filter(status="pending").count()
            if Withdraw is not None else 0
        ),
        "primary_kpis": [
            {
                "title": "صف بررسی سفارش",
                "value": (
                    Order.objects.filter(
                        status__in=["submitted", "in_review"]
                    ).count() if Order is not None else 0
                ),
                "icon": "ri-inbox-archive-line",
                "color": "primary",
                "url_name": "control_panel:orders",
            },
            {
                "title": "اختلاف باز",
                "value": (
                    Dispute.objects.filter(
                        status__in=["open", "under_review"]
                    ).count() if Dispute is not None else 0
                ),
                "icon": "ri-scales-3-line",
                "color": "danger",
                "url_name": "control_panel:backend_modules",
            },
            {
                "title": "Refund منتظر",
                "value": (
                    Refund.objects.filter(
                        status__in=["requested", "under_review"]
                    ).count() if Refund is not None else 0
                ),
                "icon": "ri-refund-2-line",
                "color": "warning",
                "url_name": "control_panel:finance",
            },
            {
                "title": "SLA معوق",
                "value": context["overdue_deadlines"],
                "icon": "ri-timer-flash-line",
                "color": "info",
                "url_name": "control_panel:deadlines",
            },
        ],
    })


def _supervisor_dashboard(user, context):
    Order = _model("orders.Order")
    Project = _model("projects.ProjectRequest")
    Penalty = _model("orders.DeliveryPenalty")

    context.update({
        "dashboard_kind": "supervisor",
        "page_title": "داشبورد ناظر",
        "hero_title": "مرکز کنترل کیفیت و بازبینی",
        "hero_subtitle": (
            "تحویل‌های منتظر بررسی، اصلاحات، پروژه‌های زیر بررسی و "
            "جریمه‌های SLA را مدیریت کنید."
        ),
        "delivery_review_count": (
            Order.objects.filter(status="delivered").count()
            if Order is not None else 0
        ),
        "client_revision_count": (
            Order.objects.filter(
                status="client_revision_requested"
            ).count() if Order is not None else 0
        ),
        "project_review_count": (
            Project.objects.filter(status="under_review").count()
            if Project is not None else 0
        ),
        "pending_penalties": (
            Penalty.objects.filter(status="pending").count()
            if Penalty is not None else 0
        ),
        "primary_kpis": [
            {
                "title": "تحویل منتظر بازبینی",
                "value": (
                    Order.objects.filter(status="delivered").count()
                    if Order is not None else 0
                ),
                "icon": "ri-shield-check-line",
                "color": "primary",
                "url_name": "control_panel:orders",
            },
            {
                "title": "اصلاح مشتری",
                "value": (
                    Order.objects.filter(
                        status="client_revision_requested"
                    ).count() if Order is not None else 0
                ),
                "icon": "ri-feedback-line",
                "color": "warning",
                "url_name": "control_panel:orders",
            },
            {
                "title": "پروژه زیر بررسی",
                "value": (
                    Project.objects.filter(
                        status="under_review"
                    ).count() if Project is not None else 0
                ),
                "icon": "ri-folder-shield-2-line",
                "color": "success",
                "url_name": "control_panel:projects",
            },
            {
                "title": "جریمه منتظر",
                "value": (
                    Penalty.objects.filter(status="pending").count()
                    if Penalty is not None else 0
                ),
                "icon": "ri-error-warning-line",
                "color": "danger",
                "url_name": "control_panel:backend_modules",
            },
        ],
    })


def _admin_dashboard(user, context):
    User = _model("accounts.User")
    Order = _model("orders.Order")
    Transaction = _model("payments.Transaction")
    Refund = _model("payments.Refund")
    Withdraw = _model("payments.WithdrawRequest")
    Dispute = _model("orders.Dispute")
    Audit = _model("operations_hub.SystemAuditLog")
    EditorProfile = _model("accounts.EditorProfile")

    successful_transactions = (
        Transaction.objects.filter(status="success")
        if Transaction is not None else None
    )

    context.update({
        "dashboard_kind": "admin",
        "page_title": "مرکز عملیات ریتاچر",
        "hero_title": "نمای جامع سلامت و عملکرد سامانه",
        "hero_subtitle": (
            "درآمد، سفارش، SLA، اختلاف، ظرفیت ادیتورها و رخدادهای "
            "سیستم را در یک مرکز کنترل مشاهده کنید."
        ),
        "user_count": User.objects.count() if User is not None else 0,
        "active_editor_count": (
            EditorProfile.objects.filter(is_available=True).count()
            if EditorProfile is not None else 0
        ),
        "commission_volume": _sum(
            successful_transactions.filter(tx_type="commission")
            if successful_transactions is not None else None,
            "amount",
        ),
        "editor_earning_volume": _sum(
            successful_transactions.filter(tx_type="editor_earning")
            if successful_transactions is not None else None,
            "amount",
        ),
        "pending_refunds": (
            Refund.objects.filter(
                status__in=["requested", "under_review"]
            ).count() if Refund is not None else 0
        ),
        "pending_withdraws": (
            Withdraw.objects.filter(status="pending").count()
            if Withdraw is not None else 0
        ),
        "open_disputes": (
            Dispute.objects.filter(
                status__in=["open", "under_review"]
            ).count() if Dispute is not None else 0
        ),
        "audit_today": (
            Audit.objects.filter(
                created_at__date=timezone.localdate()
            ).count() if Audit is not None else 0
        ),
        "editor_rating_average": (
            EditorProfile.objects.aggregate(
                value=Avg("rating_average")
            )["value"] or Decimal("0")
            if EditorProfile is not None else Decimal("0")
        ),
        "primary_kpis": [
            {
                "title": "حجم مالی موفق",
                "value": _sum(successful_transactions, "amount"),
                "suffix": " تومان",
                "icon": "ri-line-chart-line",
                "color": "primary",
                "url_name": "control_panel:finance",
                "is_money": True,
            },
            {
                "title": "کمیسیون سایت",
                "value": _sum(
                    successful_transactions.filter(
                        tx_type="commission"
                    ) if successful_transactions is not None else None,
                    "amount",
                ),
                "suffix": " تومان",
                "icon": "ri-percent-line",
                "color": "success",
                "url_name": "control_panel:finance",
                "is_money": True,
            },
            {
                "title": "SLA معوق",
                "value": context["overdue_deadlines"],
                "icon": "ri-timer-flash-line",
                "color": "danger",
                "url_name": "control_panel:deadlines",
            },
            {
                "title": "ادیتور در دسترس",
                "value": (
                    EditorProfile.objects.filter(
                        is_available=True
                    ).count() if EditorProfile is not None else 0
                ),
                "icon": "ri-team-line",
                "color": "info",
                "url_name": "control_panel:users",
            },
        ],
    })


def build_dashboard_context(user):
    context = _common_context(user)
    role = getattr(user, "role", "") or ""

    if getattr(user, "is_superuser", False) or role == "admin":
        _admin_dashboard(user, context)
    elif role == "support":
        _support_dashboard(user, context)
    elif role == "supervisor":
        _supervisor_dashboard(user, context)
    elif role == "editor":
        _editor_dashboard(user, context)
    else:
        _client_dashboard(user, context)

    context["role"] = role
    context["is_order_staff"] = is_order_staff(user)
    context["is_finance_admin"] = is_finance_admin(user)
    return context
