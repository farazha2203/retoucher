from collections import defaultdict
from decimal import Decimal

from django.apps import apps
from django.contrib import admin, messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import (
    can_view_order,
    can_view_project,
    is_finance_admin,
    is_order_staff,
    is_project_staff,
    visible_orders,
    visible_payment_requests,
    visible_project_proposals,
    visible_projects,
    visible_refunds,
    visible_transactions,
    visible_wallets,
)
from .action_bridge import (
    ORDER_ACTION_METHODS,
    PROJECT_ACTION_METHODS,
    invoke_order_action,
    invoke_project_action,
)
from .contracts import order_actions, project_actions


def _is_management(user):
    return is_order_staff(user)


def _require_management(user):
    if not is_order_staff(user):
        raise PermissionDenied


def _require_finance_admin(user):
    if not is_finance_admin(user):
        raise PermissionDenied



class PanelLoginView(auth_views.LoginView):
    template_name = "control_panel/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("control_panel:dashboard")


class PanelLogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("control_panel:login")


def _safe_model(label):
    try:
        return apps.get_model(label)
    except Exception:
        return None


def _count(label, **filters):
    model = _safe_model(label)
    if not model:
        return 0
    try:
        return model.objects.filter(**filters).count()
    except Exception:
        return 0


def _sum(label, field, **filters):
    model = _safe_model(label)
    if not model:
        return Decimal("0")
    try:
        return model.objects.filter(**filters).aggregate(total=Sum(field))["total"] or Decimal("0")
    except Exception:
        return Decimal("0")



ORDER_PROGRESS = {
    "draft": 5,
    "pending": 10,
    "submitted": 15,
    "waiting_for_payment": 20,
    "paid": 25,
    "assigned": 35,
    "accepted": 40,
    "in_progress": 55,
    "editing": 60,
    "supervisor_review": 70,
    "delivered": 80,
    "client_review": 85,
    "revision_requested": 65,
    "approved": 92,
    "settlement_pending": 95,
    "completed": 100,
    "closed": 100,
    "cancelled": 0,
}

PROJECT_PROGRESS = {
    "draft": 5,
    "submitted": 15,
    "open_for_quotes": 30,
    "open_for_samples": 35,
    "waiting_for_editor": 40,
    "under_review": 55,
    "editor_selected": 75,
    "converted_to_order": 100,
    "cancelled": 0,
    "expired": 0,
}


def _attach_order_progress(rows):
    for row in rows:
        row.panel_progress = ORDER_PROGRESS.get(row.status, 20)
    return rows


def _attach_project_progress(rows):
    for row in rows:
        row.panel_progress = PROJECT_PROGRESS.get(row.status, 20)
    return rows


def _status_choices(model):
    try:
        return list(model._meta.get_field("status").choices)
    except Exception:
        return []


def _monthly_series(model, date_field, months=8):
    if not model:
        return [], []
    start = timezone.now() - timezone.timedelta(days=31 * months)
    try:
        rows = (
            model.objects.filter(**{f"{date_field}__gte": start})
            .annotate(month=TruncMonth(date_field))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )
        labels = [row["month"].strftime("%Y-%m") for row in rows if row["month"]]
        values = [row["total"] for row in rows if row["month"]]
        return labels, values
    except Exception:
        return [], []


@login_required
def dashboard(request):
    Order = _safe_model("orders.Order")
    Project = _safe_model("projects.ProjectRequest")
    User = _safe_model("accounts.User")
    Wallet = _safe_model("payments.Wallet")
    Transaction = _safe_model("payments.Transaction")
    Withdraw = _safe_model("payments.WithdrawRequest")
    WorkflowDeadline = _safe_model("orders.WorkflowDeadline")
    Conversation = _safe_model("operations_hub.Conversation")
    ManagedFile = _safe_model("operations_hub.ManagedFile")
    Audit = _safe_model("operations_hub.SystemAuditLog")

    order_qs = visible_orders(request.user, Order.objects.all()) if Order else None
    project_qs = visible_projects(request.user, Project.objects.all()) if Project else None
    wallet_qs = visible_wallets(request.user, Wallet.objects.all()) if Wallet else None
    transaction_qs = (
        visible_transactions(request.user, Transaction.objects.all())
        if Transaction else None
    )

    order_total = order_qs.count() if order_qs is not None else 0
    completed = order_qs.filter(status__in=["completed", "paid", "closed"]).count() if order_qs is not None else 0
    active = order_qs.exclude(status__in=["draft", "cancelled", "completed", "paid", "closed"]).count() if order_qs is not None else 0
    overdue = 0
    if WorkflowDeadline and is_order_staff(request.user):
        overdue = WorkflowDeadline.objects.filter(
            status="active",
            due_at__lt=timezone.now(),
        ).count()

    order_statuses = []
    if Order:
        order_statuses = list(
            order_qs.values("status")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

    role_stats = []
    if User and is_order_staff(request.user):
        role_stats = list(
            User.objects.values("role")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

    order_month_labels, order_month_values = _monthly_series(Order, "created_at")
    project_month_labels, project_month_values = _monthly_series(Project, "created_at")

    context = {
         "page_title": (
            "داشبورد مدیریتی ریتاچر"
            if is_order_staff(request.user)
            else ("داشبورد ادیتور" if getattr(request.user, "role", "") == "editor" else "داشبورد مشتری")
        ),
        "order_total": order_total,
        "order_active": active,
        "order_completed": completed,
        "completion_percent": round((completed / order_total) * 100, 1) if order_total else 0,
        "overdue_count": overdue,
        "project_total": project_qs.count() if project_qs is not None else 0,
        "user_total": User.objects.count() if (User and is_order_staff(request.user)) else 0,
        "editor_total": User.objects.filter(role="editor").count() if (User and is_order_staff(request.user)) else 0,
        "transaction_total": transaction_qs.count() if transaction_qs is not None else 0,
        "successful_volume": (transaction_qs.filter(status="success").aggregate(total=Sum("amount"))["total"] or Decimal("0")) if transaction_qs is not None else Decimal("0"),
        "wallet_balance": (wallet_qs.aggregate(total=Sum("balance"))["total"] or Decimal("0")) if wallet_qs is not None else Decimal("0"),
        "frozen_balance": (wallet_qs.aggregate(total=Sum("frozen_balance"))["total"] or Decimal("0")) if wallet_qs is not None else Decimal("0"),
        "withdraw_pending": Withdraw.objects.filter(status="pending").count() if Withdraw else 0,
        "conversation_total": Conversation.objects.count() if Conversation else 0,
        "file_total": ManagedFile.objects.filter(deleted_at__isnull=True).count() if ManagedFile else 0,
        "audit_today": Audit.objects.filter(created_at__date=timezone.localdate()).count() if (Audit and is_order_staff(request.user)) else 0,
        "order_status_labels": [row["status"] for row in order_statuses],
        "order_status_values": [row["total"] for row in order_statuses],
        "role_labels": [row["role"] or "unknown" for row in role_stats],
        "role_values": [row["total"] for row in role_stats],
        "order_month_labels": order_month_labels,
        "order_month_values": order_month_values,
        "project_month_labels": project_month_labels,
        "project_month_values": project_month_values,
        "recent_orders": _attach_order_progress(list(
            order_qs.select_related("client", "editor").order_by("-created_at")[:8]
        )) if Order else [],
        "recent_transactions": (
            transaction_qs.select_related("wallet__user", "order").order_by("-created_at")[:8]
            if Transaction else []
        ),
        "recent_audits": (
            Audit.objects.select_related("actor").order_by("-created_at")[:8]
            if Audit else []
        ),
    }
    return render(request, "control_panel/dashboard.html", context)


@login_required
def orders_list(request):
    Order = _safe_model("orders.Order")
    rows = []
    if Order:
        rows = _attach_order_progress(list(visible_orders(request.user, Order.objects.select_related("client", "editor")).order_by("-created_at")[:300]))
    return render(request, "control_panel/orders.html", {"page_title": "سفارش‌ها", "rows": rows})



def _order_workspace_context(request, order):
    Activity = _safe_model("orders.OrderActivityLog")
    StatusHistory = _safe_model("orders.OrderStatusHistory")
    Notification = _safe_model("orders.OrderNotification")
    Comment = _safe_model("orders.OrderComment")

    activities = list(Activity.objects.filter(order=order).select_related("actor").order_by("-created_at", "-id")[:250]) if Activity else []
    status_history = list(StatusHistory.objects.filter(order=order).select_related("changed_by").order_by("-created_at", "-id")[:150]) if StatusHistory else []
    order_notifications = list(Notification.objects.filter(order=order).select_related("recipient", "actor").order_by("-created_at", "-id")[:150]) if Notification else []
    comments = list(Comment.objects.filter(order=order, parent__isnull=True).select_related("sender", "resolved_by").prefetch_related("replies__sender").order_by("-created_at", "-id")[:150]) if Comment else []
    deliveries = list(order.deliveries.select_related("uploaded_by", "publication_requested_by", "publication_reviewed_by").order_by("-uploaded_at", "-id"))
    revisions = list(order.revisions.select_related("requested_by").order_by("-created_at", "-id"))
    ratings = list(order.ratings.select_related("rated_by").order_by("-created_at", "-id"))
    images = list(order.images.order_by("uploaded_at", "id"))
    deadlines = list(order.workflow_deadlines.order_by("-created_at", "-id"))
    transactions = list(order.transactions.select_related("wallet__user").order_by("-created_at", "-id")[:100])
    payment_requests = list(order.payment_requests.select_related("user").order_by("-created_at", "-id")[:100])
    managed_files = list(order.managed_files.filter(deleted_at__isnull=True).select_related("uploaded_by").order_by("-created_at", "-id"))
    conversations = list(order.panel_conversations.prefetch_related("participants").order_by("-last_message_at", "-id"))
    return {
        "activities": activities, "status_history": status_history,
        "order_notifications": order_notifications, "comments": comments,
        "deliveries": deliveries, "revisions": revisions, "ratings": ratings,
        "images": images, "deadlines": deadlines, "transactions": transactions,
        "payment_requests": payment_requests, "managed_files": managed_files,
        "conversations": conversations,
        "unresolved_comments": sum(1 for x in comments if not x.resolved_at),
        "active_deadlines": sum(1 for x in deadlines if x.status == "active"),
        "workspace_counts": {"images": len(images), "deliveries": len(deliveries), "revisions": len(revisions), "comments": len(comments), "files": len(managed_files), "conversations": len(conversations), "transactions": len(transactions)},
    }


def _project_workspace_context(request, project):
    proposals = visible_project_proposals(request.user, project, project.proposals.select_related("editor", "editor__user", "reviewed_by").order_by("-submitted_at", "-id"))
    images = list(project.images.order_by("sort_order", "uploaded_at", "id"))
    activities = list(project.activities.select_related("actor").order_by("-created_at", "-id")[:200])
    files = list(project.managed_files.filter(deleted_at__isnull=True).select_related("uploaded_by").order_by("-created_at", "-id"))
    conversations = list(project.panel_conversations.prefetch_related("participants").order_by("-last_message_at", "-id"))
    deadlines = list(project.workflow_deadlines.order_by("-created_at", "-id"))
    return {
        "visible_proposals": proposals, "project_images": images,
        "project_activities": activities, "project_files": files,
        "project_conversations": conversations, "project_deadlines": deadlines,
        "project_workspace_counts": {"images": len(images), "proposals": proposals.count(), "activities": len(activities), "files": len(files), "conversations": len(conversations)},
    }

@login_required
def order_detail(request, pk):
    Order = _safe_model("orders.Order")
    if not Order:
        raise PermissionDenied
    order = get_object_or_404(
        Order.objects.select_related("client", "editor").prefetch_related(
            "images", "deliveries", "revisions", "ratings", "comments",
            "workflow_deadlines", "transactions", "payment_requests",
            "managed_files", "panel_conversations",
        ), pk=pk,
    )
    if not can_view_order(request.user, order):
        raise PermissionDenied
    User = _safe_model("accounts.User")
    context = {
        "page_title": f"سفارش #{order.pk}", "order": order,
        "editors": User.objects.filter(role="editor", is_active=True).select_related("editor_profile").order_by("-editor_profile__rating_average", "username") if User else [],
        "system_admin_url": reverse("admin:orders_order_change", args=[order.pk]),
        "progress_percent": ORDER_PROGRESS.get(order.status, 20),
        "allowed_actions": order_actions(request.user, order),
        "is_order_staff": is_order_staff(request.user),
        "is_order_owner": order.client_id == request.user.id,
        "is_assigned_editor": order.editor_id == request.user.id,
    }
    context.update(_order_workspace_context(request, order))
    return render(request, "control_panel/order_detail.html", context)



@login_required
def projects_list(request):
    Project = _safe_model("projects.ProjectRequest")
    rows = []
    if Project:
        rows = _attach_project_progress(list(visible_projects(request.user, Project.objects.select_related(
            "client", "target_editor__user", "edit_style", "package", "converted_order"
        )).annotate(proposal_count=Count("proposals")).order_by("-created_at")[:300]))
    return render(request, "control_panel/projects.html", {"page_title": "پروژه‌ها و درخواست‌ها", "rows": rows})


@login_required
def project_detail(request, pk):
    Project = _safe_model("projects.ProjectRequest")
    if not Project:
        raise PermissionDenied
    project = get_object_or_404(
        Project.objects.select_related("client", "target_editor__user", "edit_style", "package", "converted_order").prefetch_related("images", "proposals__editor__user", "activities", "managed_files", "panel_conversations", "workflow_deadlines"), pk=pk,
    )
    if not can_view_project(request.user, project):
        raise PermissionDenied
    context = {
        "page_title": f"پروژه #{project.pk}", "project": project,
        "allowed_actions": project_actions(request.user, project),
        "system_admin_url": reverse("admin:projects_projectrequest_change", args=[project.pk]),
        "progress_percent": PROJECT_PROGRESS.get(project.status, 20),
        "is_project_staff": is_project_staff(request.user),
        "is_project_owner": project.client_id == request.user.id,
    }
    context.update(_project_workspace_context(request, project))
    return render(request, "control_panel/project_detail.html", context)



@login_required
@require_POST
def order_change_status(request, pk):
    _require_management(request.user)
    Order = _safe_model("orders.Order")
    Activity = _safe_model("orders.OrderActivityLog")
    if not Order:
        raise PermissionDenied

    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get("status", "").strip()
    valid_statuses = {value for value, _label in _status_choices(Order)}

    if new_status not in valid_statuses:
        messages.error(request, "وضعیت انتخاب‌شده معتبر نیست.")
        return redirect("control_panel:order_detail", pk=pk)

    old_status = order.status
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    if Activity:
        try:
            Activity.objects.create(
                order=order,
                actor=request.user,
                activity_type="status_changed",
                message=f"وضعیت از {old_status} به {new_status} تغییر کرد.",
                metadata={"from_status": old_status, "to_status": new_status, "source": "velzon_panel"},
            )
        except Exception:
            pass

    messages.success(request, "وضعیت سفارش با موفقیت تغییر کرد.")
    return redirect("control_panel:order_detail", pk=pk)


@login_required
@require_POST
def order_assign_editor(request, pk):
    _require_management(request.user)
    Order = _safe_model("orders.Order")
    User = _safe_model("accounts.User")
    if not Order or not User:
        raise PermissionDenied

    order = get_object_or_404(Order, pk=pk)
    editor_id = request.POST.get("editor_id", "").strip()

    if not editor_id:
        order.editor = None
    else:
        editor = get_object_or_404(User, pk=editor_id, role="editor", is_active=True)
        order.editor = editor
        if order.status in {"draft", "pending", "submitted"}:
            order.status = "assigned"

    update_fields = ["editor", "updated_at"]
    if hasattr(order, "status"):
        update_fields.append("status")
    order.save(update_fields=update_fields)

    messages.success(request, "ادیتور سفارش به‌روزرسانی شد.")
    return redirect("control_panel:order_detail", pk=pk)


@login_required
@require_POST
def project_change_status(request, pk):
    _require_management(request.user)
    Project = _safe_model("projects.ProjectRequest")
    Activity = _safe_model("projects.ProjectRequestActivity")
    if not Project:
        raise PermissionDenied

    project = get_object_or_404(Project, pk=pk)
    new_status = request.POST.get("status", "").strip()
    valid_statuses = {value for value, _label in _status_choices(Project)}

    if new_status not in valid_statuses:
        messages.error(request, "وضعیت انتخاب‌شده معتبر نیست.")
        return redirect("control_panel:project_detail", pk=pk)

    old_status = project.status
    project.status = new_status
    project.save(update_fields=["status", "updated_at"])

    if Activity:
        try:
            Activity.objects.create(
                project_request=project,
                actor=request.user,
                action="status_changed",
                message=f"وضعیت از {old_status} به {new_status} تغییر کرد.",
                metadata={"from_status": old_status, "to_status": new_status, "source": "velzon_panel"},
            )
        except Exception:
            pass

    messages.success(request, "وضعیت پروژه با موفقیت تغییر کرد.")
    return redirect("control_panel:project_detail", pk=pk)



@login_required
@require_POST
def order_workflow_action(request, pk, action_key):
    order_model = _safe_model("orders.Order")
    order = get_object_or_404(order_model, pk=pk)

    if not can_view_order(request.user, order):
        raise PermissionDenied

    allowed = {item.key for item in order_actions(request.user, order)}
    if action_key not in allowed or action_key not in ORDER_ACTION_METHODS:
        raise PermissionDenied("این عملیات در مرحله فعلی برای شما مجاز نیست.")

    response = invoke_order_action(request, pk, action_key)
    if 200 <= response.status_code < 300:
        messages.success(request, "عملیات با موفقیت انجام شد.")
    else:
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        messages.error(request, detail or "عملیات انجام نشد. اطلاعات فرم را بررسی کنید.")
    return redirect("control_panel:order_detail", pk=pk)


@login_required
@require_POST
def project_workflow_action(request, pk, action_key):
    project_model = _safe_model("projects.ProjectRequest")
    project = get_object_or_404(project_model, pk=pk)

    if not can_view_project(request.user, project):
        raise PermissionDenied

    allowed = {item.key for item in project_actions(request.user, project)}
    if action_key not in allowed or action_key not in PROJECT_ACTION_METHODS:
        raise PermissionDenied("این عملیات در مرحله فعلی برای شما مجاز نیست.")

    response = invoke_project_action(request, pk, action_key)
    if 200 <= response.status_code < 300:
        messages.success(request, "عملیات پروژه با موفقیت انجام شد.")
    else:
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        if not detail and isinstance(response.data, dict):
            detail = "؛ ".join(f"{key}: {value}" for key, value in response.data.items())
        messages.error(request, detail or "عملیات پروژه انجام نشد.")
    return redirect("control_panel:project_detail", pk=pk)



@login_required
def users_list(request):
    _require_management(request.user)
    User = _safe_model("accounts.User")
    rows = User.objects.order_by("-date_joined")[:300] if User else []
    return render(request, "control_panel/users.html", {"page_title": "کاربران", "rows": rows})


@login_required
def finance_dashboard(request):
    Wallet = _safe_model("payments.Wallet")
    Transaction = _safe_model("payments.Transaction")
    PaymentRequest = _safe_model("payments.PaymentRequest")
    WithdrawRequest = _safe_model("payments.WithdrawRequest")
    Refund = _safe_model("payments.Refund")
    Commission = _safe_model("payments.SiteCommissionSetting")
    refunds_qs = visible_refunds(request.user, Refund.objects.all()) if Refund else None

    wallet_qs = (
        visible_wallets(request.user, Wallet.objects.all())
        if Wallet else None
    )
    transaction_qs = (
        visible_transactions(request.user, Transaction.objects.all())
        if Transaction else None
    )
    payment_request_qs = (
        visible_payment_requests(request.user, PaymentRequest.objects.all())
        if PaymentRequest else None
    )

    tx_type_stats = []
    if transaction_qs is not None:
        tx_type_stats = list(
            transaction_qs.values("tx_type")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

    context = {
        "page_title": "مدیریت مالی",
        "wallets": wallet_qs.select_related("user").order_by("-balance")[:100] if wallet_qs is not None else [],
        "transactions": transaction_qs.select_related("wallet__user", "order").order_by("-created_at")[:100] if transaction_qs is not None else [],
        "payment_requests": payment_request_qs.select_related("user", "order").order_by("-created_at")[:50] if payment_request_qs is not None else [],
        "withdraws": (
            WithdrawRequest.objects.select_related("editor", "reviewed_by").order_by("-created_at")[:50]
            if (WithdrawRequest and is_finance_admin(request.user))
            else (
                WithdrawRequest.objects.filter(editor=request.user).select_related("editor", "reviewed_by").order_by("-created_at")[:50]
                if (WithdrawRequest and getattr(request.user, "role", "") == "editor")
                else []
            )
        ),
        "refunds": refunds_qs.select_related("order", "requested_by", "reviewed_by").order_by("-requested_at")[:50] if refunds_qs is not None else [],
        "commission": Commission.get_active() if (Commission and is_finance_admin(request.user)) else None,
        "is_finance_admin": is_finance_admin(request.user),
        "wallet_total": (wallet_qs.aggregate(total=Sum("balance"))["total"] or Decimal("0")) if wallet_qs is not None else Decimal("0"),
        "wallet_frozen": (wallet_qs.aggregate(total=Sum("frozen_balance"))["total"] or Decimal("0")) if wallet_qs is not None else Decimal("0"),
        "withdrawable_total": (wallet_qs.aggregate(total=Sum("withdrawable_balance"))["total"] or Decimal("0")) if wallet_qs is not None else Decimal("0"),
        "successful_volume": (transaction_qs.filter(status="success").aggregate(total=Sum("amount"))["total"] or Decimal("0")) if transaction_qs is not None else Decimal("0"),
        "tx_type_labels": [row["tx_type"] for row in tx_type_stats],
        "tx_type_values": [int(row["total"] or 0) for row in tx_type_stats],
    }
    return render(request, "control_panel/finance.html", context)


@login_required
def notifications_center(request):
    Notification = _safe_model("notifications.Notification")
    OrderNotification = _safe_model("orders.OrderNotification")
    notifications = Notification.objects.select_related("recipient").order_by("-created_at") if Notification else None
    order_notifications = OrderNotification.objects.select_related("recipient", "actor", "order").order_by("-created_at") if OrderNotification else None

    if notifications is not None:
        notifications = notifications.filter(recipient=request.user)
    if order_notifications is not None:
        order_notifications = order_notifications.filter(recipient=request.user)

    return render(
        request,
        "control_panel/notifications.html",
        {
            "page_title": "مرکز اعلان‌ها",
            "notifications": notifications[:200] if notifications is not None else [],
            "order_notifications": order_notifications[:200] if order_notifications is not None else [],
        },
    )


@login_required
def deadlines_center(request):
    _require_management(request.user)
    Deadline = _safe_model("orders.WorkflowDeadline")
    rows = Deadline.objects.select_related("order", "project_request").order_by("due_at")[:300] if Deadline else []
    return render(request, "control_panel/deadlines.html", {"page_title": "مرکز SLA و مهلت‌ها", "rows": rows})


@login_required
def backend_modules(request):
    _require_management(request.user)
    groups = defaultdict(list)
    for model, model_admin in admin.site._registry.items():
        opts = model._meta
        try:
            count = model.objects.count()
        except Exception:
            count = 0
        groups[opts.app_label].append({
            "label": str(opts.verbose_name_plural),
            "model_name": opts.model_name,
            "count": count,
            "list_url": reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"),
            "add_url": reverse(f"admin:{opts.app_label}_{opts.model_name}_add") if model_admin.has_add_permission(request) else "",
        })
    modules = [{"app": app, "models": sorted(items, key=lambda item: item["label"])} for app, items in sorted(groups.items())]
    return render(request, "control_panel/backend_modules.html", {"page_title": "همه امکانات Backend", "modules": modules})


@login_required
def settings_home(request):
    return render(
        request,
        "control_panel/placeholder.html",
        {
            "page_title": "تنظیمات",
            "section_title": "تنظیمات سامانه",
            "section_description": "تنظیمات عمومی، امنیت، نقش‌ها و Workflow از مرکز Backend قابل مدیریت است.",
        },
    )
