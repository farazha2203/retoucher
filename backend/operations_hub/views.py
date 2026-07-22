import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ConversationCreateForm, ManagedFileUploadForm
from .models import (
    Conversation,
    ConversationParticipant,
    FileDownloadLog,
    ManagedFile,
    Message,
    MessageAttachment,
    SystemAuditLog,
)
from .permissions import can_access_conversation, is_management, visible_conversations, visible_files


def _ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


@login_required
def messages_home(request):
    conversations = visible_conversations(
        request.user,
        Conversation.objects.select_related("order", "project_request").prefetch_related("participants"),
    )
    return render(
        request,
        "control_panel/messages.html",
        {
            "page_title": "پیام‌ها و گفتگوها",
            "conversations": conversations,
            "conversation": None,
            "chat_messages": [],
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("order", "project_request").prefetch_related("participants"),
        pk=pk,
    )
    if not can_access_conversation(request.user, conversation):
        raise PermissionDenied

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        uploaded_files = request.FILES.getlist("attachments")

        if body or uploaded_files:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body,
                message_type=Message.Type.FILE if uploaded_files and not body else Message.Type.TEXT,
            )
            for uploaded in uploaded_files:
                MessageAttachment.objects.create(
                    message=message,
                    file=uploaded,
                    original_name=uploaded.name,
                    mime_type=getattr(uploaded, "content_type", "") or "",
                    size_bytes=getattr(uploaded, "size", 0) or 0,
                )
            conversation.last_message_at = timezone.now()
            conversation.save(update_fields=["last_message_at", "updated_at"])

        return redirect("control_panel:conversation_detail", pk=conversation.pk)

    ConversationParticipant.objects.filter(
        conversation=conversation,
        user=request.user,
    ).update(last_read_at=timezone.now())

    conversations = visible_conversations(request.user, Conversation.objects.all())
    chat_messages = conversation.messages.select_related("sender", "reply_to").prefetch_related("attachments")
    return render(
        request,
        "control_panel/messages.html",
        {
            "page_title": conversation.title,
            "conversations": conversations,
            "conversation": conversation,
            "chat_messages": chat_messages,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def conversation_create(request):
    if not is_management(request.user):
        raise PermissionDenied

    form = ConversationCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        conversation = form.save(commit=False)
        conversation.created_by = request.user
        conversation.save()

        participant_ids = {
            int(value)
            for value in request.POST.getlist("participant_ids")
            if str(value).isdigit()
        }
        participant_ids.add(request.user.pk)

        if conversation.order_id:
            participant_ids.update(
                value for value in [conversation.order.client_id, conversation.order.editor_id] if value
            )
        if conversation.project_request_id:
            participant_ids.update(
                value
                for value in [
                    conversation.project_request.client_id,
                    conversation.project_request.target_editor_id,
                ]
                if value
            )

        ConversationParticipant.objects.bulk_create(
            [
                ConversationParticipant(
                    conversation=conversation,
                    user_id=user_id,
                    is_admin=user_id == request.user.pk,
                )
                for user_id in participant_ids
            ],
            ignore_conflicts=True,
        )
        return redirect("control_panel:conversation_detail", pk=conversation.pk)

    from accounts.models import User

    return render(
        request,
        "control_panel/conversation_form.html",
        {
            "page_title": "گفتگوی جدید",
            "form": form,
            "users": User.objects.filter(is_active=True).order_by("username"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def files_home(request):
    queryset = visible_files(
        request.user,
        ManagedFile.objects.select_related("uploaded_by", "order", "project_request").filter(deleted_at__isnull=True),
    )
    form = ManagedFileUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.uploaded_by = request.user
        uploaded = request.FILES.get("file")
        if uploaded:
            item.size_bytes = uploaded.size or 0
            item.mime_type = getattr(uploaded, "content_type", "") or mimetypes.guess_type(uploaded.name)[0] or ""
        item.save()
        messages.success(request, "فایل با موفقیت بارگذاری شد.")
        return redirect("control_panel:files")

    return render(
        request,
        "control_panel/files.html",
        {
            "page_title": "مدیریت فایل‌ها",
            "files": queryset[:250],
            "upload_form": form,
        },
    )


@login_required
def file_download(request, pk):
    item = get_object_or_404(ManagedFile, pk=pk, deleted_at__isnull=True)
    if not visible_files(request.user, ManagedFile.objects.filter(pk=item.pk)).exists():
        raise PermissionDenied

    ManagedFile.objects.filter(pk=item.pk).update(download_count=F("download_count") + 1)
    FileDownloadLog.objects.create(
        managed_file=item,
        user=request.user,
        ip_address=_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
    return FileResponse(item.file.open("rb"), as_attachment=True, filename=item.filename)


@login_required
@require_POST
def file_delete(request, pk):
    item = get_object_or_404(ManagedFile, pk=pk, deleted_at__isnull=True)
    if not (is_management(request.user) or item.uploaded_by_id == request.user.pk):
        raise PermissionDenied
    item.deleted_at = timezone.now()
    item.save(update_fields=["deleted_at", "updated_at"])
    messages.success(request, "فایل به سطل بازیافت منتقل شد.")
    return redirect("control_panel:files")


@login_required
def audit_home(request):
    if not is_management(request.user):
        raise PermissionDenied

    query = request.GET.get("q", "").strip()
    level = request.GET.get("level", "").strip()
    logs = SystemAuditLog.objects.select_related("actor")

    if query:
        logs = logs.filter(
            Q(action__icontains=query)
            | Q(message__icontains=query)
            | Q(path__icontains=query)
            | Q(actor__username__icontains=query)
        )
    if level:
        logs = logs.filter(level=level)

    try:
        from orders.models import OrderActivityLog
        order_logs = OrderActivityLog.objects.select_related("order", "actor").order_by("-created_at")[:100]
    except Exception:
        order_logs = []

    return render(
        request,
        "control_panel/audit.html",
        {
            "page_title": "مرکز لاگ و گزارش",
            "logs": logs[:300],
            "order_logs": order_logs,
            "query": query,
            "selected_level": level,
            "levels": SystemAuditLog.Level.choices,
        },
    )
