from collections import defaultdict
from decimal import Decimal

from django.apps import apps
from django.contrib import admin, messages
from django.contrib.auth import get_user_model, views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from rest_framework.test import APIRequestFactory, force_authenticate

from orders.views import OrderViewSet
from projects.views import ProjectRequestViewSet

from .forms import (
    AdminUserCreateForm,
    AdminUserUpdateForm,
    EditorProfileAdminForm,
    PanelOrderCreateForm,
    PanelProjectCreateForm,
)


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
from .dashboard_engine import build_dashboard_context


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
    context = build_dashboard_context(request.user)
    return render(request, "control_panel/dashboard.html", context)


def _add_drf_errors_to_form(form, errors):
    if not isinstance(errors, dict):
        form.add_error(None, str(errors))
        return

    for field_name, messages_list in errors.items():
        target = field_name if field_name in form.fields else None
        if isinstance(messages_list, (list, tuple)):
            for message in messages_list:
                form.add_error(target, str(message))
        else:
            form.add_error(target, str(messages_list))


def _execute_create_viewset(*, request, viewset_class, path, data):
    factory = APIRequestFactory()
    api_request = factory.post(path, data=data, format="multipart")
    force_authenticate(api_request, user=request.user)
    api_view = viewset_class.as_view({"post": "create"})
    return api_view(api_request)


@login_required
def order_create(request):
    if getattr(request.user, "role", "") != "client":
        raise PermissionDenied

    form = PanelOrderCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        payload = {
            "title": form.cleaned_data["title"],
            "description": form.cleaned_data.get("description") or "",
        }
        deadline = form.cleaned_data.get("deadline")
        if deadline:
            payload["deadline"] = deadline.isoformat()

        api_response = _execute_create_viewset(
            request=request,
            viewset_class=OrderViewSet,
            path="/api/orders/",
            data=payload,
        )

        if api_response.status_code == 201:
            order_id = api_response.data["id"]
            messages.success(
                request,
                "سفارش با موفقیت ایجاد شد. اکنون فایل‌ها را اضافه و سفارش را ارسال کنید.",
            )
            return redirect("control_panel:order_detail", pk=order_id)

        _add_drf_errors_to_form(form, api_response.data)

    return render(
        request,
        "control_panel/order_create.html",
        {
            "page_title": "ثبت سفارش جدید",
            "form": form,
        },
    )


@login_required
def project_create(request):
    if getattr(request.user, "role", "") != "client":
        raise PermissionDenied

    form = PanelProjectCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        cleaned = form.cleaned_data
        payload = {
            "request_type": cleaned["request_type"],
            "title": cleaned["title"],
            "description": cleaned.get("description") or "",
            "edit_style": cleaned["edit_style"].pk,
            "budget_min": cleaned.get("budget_min") or 0,
            "budget_max": cleaned.get("budget_max") or 0,
            "client_note": cleaned.get("client_note") or "",
        }

        if cleaned.get("package"):
            payload["package"] = cleaned["package"].pk
        if cleaned.get("target_editor"):
            payload["target_editor"] = cleaned["target_editor"].pk
        if cleaned.get("preferred_deadline"):
            payload["preferred_deadline"] = (
                cleaned["preferred_deadline"].isoformat()
            )

        api_response = _execute_create_viewset(
            request=request,
            viewset_class=ProjectRequestViewSet,
            path="/api/projects/requests/",
            data=payload,
        )

        if api_response.status_code == 201:
            project_id = api_response.data["id"]
            messages.success(
                request,
                "پروژه با موفقیت ثبت شد و Workflow مربوط به نوع درخواست فعال گردید.",
            )
            return redirect(
                "control_panel:project_detail",
                pk=project_id,
            )

        _add_drf_errors_to_form(form, api_response.data)

    return render(
        request,
        "control_panel/project_create.html",
        {
            "page_title": "ثبت پروژه جدید",
            "form": form,
            "request_type_help": {
                "direct_editor": "ارسال مستقیم درخواست برای یک ادیتور مشخص",
                "public_quote": "دریافت پیشنهاد قیمت از ادیتورهای واجد شرایط",
                "sample_challenge": "دریافت نمونه و بررسی توسط ناظر",
                "managed_order": "انتخاب و تخصیص ادیتور توسط مدیریت",
            },
        },
    )


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
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "admin"
    ):
        raise PermissionDenied

    User = get_user_model()
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    state = request.GET.get("state", "").strip()

    rows = User.objects.select_related("editor_profile").order_by(
        "-is_active",
        "-date_joined",
        "-id",
    )

    if query:
        rows = rows.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone_number__icontains=query)
        )
    if role:
        rows = rows.filter(role=role)
    if state == "active":
        rows = rows.filter(is_active=True)
    elif state == "inactive":
        rows = rows.filter(is_active=False)
    elif state == "verified":
        rows = rows.filter(is_verified=True)

    role_stats = list(
        User.objects.values("role")
        .annotate(total=Count("id"))
        .order_by("role")
    )

    return render(
        request,
        "control_panel/users.html",
        {
            "page_title": "کاربران و ادیتورها",
            "rows": rows[:500],
            "query": query,
            "selected_role": role,
            "selected_state": state,
            "role_choices": User.Role.choices,
            "role_stats": role_stats,
            "active_count": User.objects.filter(is_active=True).count(),
            "inactive_count": User.objects.filter(is_active=False).count(),
            "verified_count": User.objects.filter(is_verified=True).count(),
            "editor_count": User.objects.filter(role=User.Role.EDITOR).count(),
        },
    )


@login_required
def user_create(request):
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "admin"
    ):
        raise PermissionDenied

    form = AdminUserCreateForm(
        request.POST or None,
        actor=request.user,
    )
    editor_form = EditorProfileAdminForm(
        request.POST or None,
        prefix="editor",
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()

        if user.role == user.Role.EDITOR:
            profile, _ = user.editor_profile.__class__.objects.get_or_create(
                user=user,
                defaults={"display_name": user.get_full_name() or user.username},
            ) if hasattr(user, "editor_profile") else (None, False)

            if profile is None:
                from accounts.models import EditorProfile
                profile = EditorProfile.objects.create(
                    user=user,
                    display_name=user.get_full_name() or user.username,
                )

            if editor_form.is_valid():
                for field, value in editor_form.cleaned_data.items():
                    if field == "skills":
                        continue
                    setattr(profile, field, value)
                profile.save()
                profile.skills.set(editor_form.cleaned_data.get("skills", []))

        messages.success(request, "کاربر جدید با موفقیت ایجاد شد.")
        return redirect("control_panel:user_edit", pk=user.pk)

    return render(
        request,
        "control_panel/user_form.html",
        {
            "page_title": "ایجاد کاربر جدید",
            "form": form,
            "editor_form": editor_form,
            "creating": True,
        },
    )


@login_required
def user_edit(request, pk):
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "admin"
    ):
        raise PermissionDenied

    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied

    form = AdminUserUpdateForm(
        request.POST or None,
        instance=user_obj,
        actor=request.user,
    )

    from accounts.models import EditorProfile
    profile = EditorProfile.objects.filter(user=user_obj).first()
    editor_form = EditorProfileAdminForm(
        request.POST or None,
        instance=profile,
        prefix="editor",
    )

    if request.method == "POST" and form.is_valid():
        updated = form.save()

        if updated.role == updated.Role.EDITOR:
            profile, _ = EditorProfile.objects.get_or_create(
                user=updated,
                defaults={
                    "display_name": updated.get_full_name() or updated.username,
                },
            )
            editor_form = EditorProfileAdminForm(
                request.POST,
                instance=profile,
                prefix="editor",
            )
            if editor_form.is_valid():
                editor_form.save()
        elif profile is not None:
            profile.is_available = False
            profile.save(update_fields=["is_available", "updated_at"])

        messages.success(request, "اطلاعات کاربر ذخیره شد.")
        return redirect("control_panel:user_edit", pk=updated.pk)

    return render(
        request,
        "control_panel/user_form.html",
        {
            "page_title": f"ویرایش {user_obj.username}",
            "form": form,
            "editor_form": editor_form,
            "user_obj": user_obj,
            "profile": profile,
            "creating": False,
        },
    )


@login_required
@require_POST
def user_toggle_active(request, pk):
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "admin"
    ):
        raise PermissionDenied

    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj.pk == request.user.pk:
        messages.error(request, "نمی‌توانید حساب فعال خودتان را غیرفعال کنید.")
        return redirect("control_panel:user_edit", pk=pk)

    if user_obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        "حساب کاربر فعال شد." if user_obj.is_active
        else "حساب کاربر غیرفعال شد.",
    )
    return redirect(request.POST.get("next") or "control_panel:users")


@login_required
@require_POST
def user_toggle_verified(request, pk):
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "admin"
    ):
        raise PermissionDenied

    User = get_user_model()
    user_obj = get_object_or_404(User, pk=pk)
    user_obj.is_verified = not user_obj.is_verified
    user_obj.save(update_fields=["is_verified", "updated_at"])

    messages.success(
        request,
        "کاربر تأیید شد." if user_obj.is_verified
        else "تأیید کاربر برداشته شد.",
    )
    return redirect(request.POST.get("next") or "control_panel:users")



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
    if not (
        request.user.is_superuser
        or getattr(request.user, "role", "") == "admin"
    ):
        raise PermissionDenied

    groups = defaultdict(list)
    total_models = 0
    total_records = 0

    app_labels = {
        "auth": "احراز هویت و گروه‌ها",
        "accounts": "کاربران و ادیتورها",
        "catalog": "کاتالوگ خدمات",
        "orders": "سفارش‌ها و Workflow",
        "projects": "پروژه‌ها و پیشنهادها",
        "payments": "مالی و تسویه",
        "notifications": "اعلان‌ها",
        "operations_hub": "چت، فایل و لاگ",
        "sb_admin_audit": "لاگ پنل قدیمی",
    }

    dedicated_models = {
        "accounts.user",
        "accounts.editorprofile",
        "orders.order",
        "projects.projectrequest",
        "payments.wallet",
        "payments.transaction",
        "notifications.notification",
        "operations_hub.conversation",
        "operations_hub.managedfile",
        "operations_hub.systemauditlog",
    }

    for model, model_admin in admin.site._registry.items():
        opts = model._meta
        key = f"{opts.app_label}.{opts.model_name}"

        try:
            count = model.objects.count()
        except Exception:
            count = 0

        total_models += 1
        total_records += count

        try:
            list_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_changelist"
            )
        except Exception:
            list_url = ""

        add_url = ""
        try:
            if model_admin.has_add_permission(request):
                add_url = reverse(
                    f"admin:{opts.app_label}_{opts.model_name}_add"
                )
        except Exception:
            add_url = ""

        groups[opts.app_label].append({
            "label": str(opts.verbose_name_plural),
            "model_name": opts.model_name,
            "count": count,
            "list_url": list_url,
            "add_url": add_url,
            "has_dedicated_page": key in dedicated_models,
        })

    modules = [
        {
            "app": app,
            "label": app_labels.get(app, app.replace("_", " ").title()),
            "models": sorted(items, key=lambda item: item["label"]),
            "count": sum(item["count"] for item in items),
        }
        for app, items in sorted(groups.items())
    ]

    return render(
        request,
        "control_panel/settings.html",
        {
            "page_title": "تنظیمات و امکانات مدیریتی",
            "modules": modules,
            "total_models": total_models,
            "total_records": total_records,
            "dedicated_count": len(dedicated_models),
            "legacy_count": max(total_models - len(dedicated_models), 0),
        },
    )

