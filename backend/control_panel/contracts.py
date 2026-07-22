from dataclasses import dataclass


@dataclass(frozen=True)
class PanelAction:
    key: str
    label: str
    style: str = "primary"
    icon: str = "ri-play-circle-line"
    requires_note: bool = False
    requires_file: bool = False
    requires_editor: bool = False
    requires_rating: bool = False
    confirm: str = ""


def order_actions(user, order):
    role = getattr(user, "role", "")
    staff = bool(user.is_staff or role in {"admin", "support", "supervisor"})
    owner = order.client_id == user.id
    assigned_editor = order.editor_id == user.id
    actions = []

    if owner and order.status == "draft":
        actions.append(PanelAction("submit", "ارسال برای بررسی", "primary", "ri-send-plane-line"))
        actions.append(PanelAction("upload_image", "افزودن تصویر", "info", "ri-image-add-line", requires_file=True))

    if staff and order.status == "submitted":
        actions.append(PanelAction("start_review", "شروع بررسی", "warning", "ri-search-eye-line"))

    if staff and order.status == "in_review":
        actions.append(PanelAction("assign_editor", "تخصیص ادیتور", "primary", "ri-user-add-line", requires_editor=True))

    if assigned_editor and order.status == "assigned":
        actions.append(PanelAction("start_work", "شروع کار", "success", "ri-play-line"))

    if assigned_editor and order.status == "in_progress":
        actions.append(PanelAction("deliver", "ارسال خروجی", "success", "ri-upload-cloud-line", requires_file=True, requires_note=True))

    if staff and order.status == "delivered":
        actions.extend([
            PanelAction("supervisor_approve", "تأیید ناظر و ارسال برای مشتری", "success", "ri-checkbox-circle-line", requires_rating=True),
            PanelAction("supervisor_request_revision", "درخواست اصلاح ناظر", "warning", "ri-restart-line", requires_note=True),
        ])

    if owner and order.status == "client_review":
        actions.extend([
            PanelAction("client_approve", "تأیید نهایی سفارش", "success", "ri-shield-check-line", confirm="آیا خروجی نهایی را تأیید می‌کنید؟"),
            PanelAction("client_request_revision", "درخواست اصلاح", "warning", "ri-edit-2-line", requires_note=True),
        ])

    if staff and order.status == "client_revision_requested":
        actions.extend([
            PanelAction("supervisor_accept_client_revision", "پذیرش اصلاح مشتری", "success", "ri-check-double-line", requires_note=True),
            PanelAction("supervisor_reject_client_revision", "رد درخواست اصلاح", "danger", "ri-close-circle-line", requires_note=True),
        ])

    if assigned_editor and order.status == "revision_required":
        actions.append(PanelAction("start_revision", "شروع اصلاح", "warning", "ri-tools-line"))

    return actions


def project_actions(user, project):
    role = getattr(user, "role", "")
    is_staff = bool(user.is_staff)
    owner = project.client_id == user.id
    profile = getattr(user, "editor_profile", None)
    target = bool(profile and project.target_editor_id == profile.id)
    matching = bool(profile and project.edit_style_id and profile.skills.filter(id=project.edit_style_id).exists())
    actions = []

    if owner:
        actions.append(PanelAction("upload_image", "افزودن تصویر", "info", "ri-image-add-line", requires_file=True))

    if target and project.request_type == "direct_editor" and project.status == "waiting_for_editor":
        actions.extend([
            PanelAction("direct_proposal", "ارسال پیشنهاد مستقیم", "success", "ri-file-list-3-line"),
            PanelAction("direct_decline", "رد درخواست مستقیم", "danger", "ri-close-circle-line", requires_note=True),
        ])

    if profile and matching and project.request_type == "public_quote" and project.status == "open_for_quotes":
        actions.append(PanelAction("public_proposal", "ارسال پیشنهاد قیمت", "success", "ri-money-dollar-circle-line"))

    if profile and matching and project.request_type == "sample_challenge" and project.status == "open_for_samples":
        actions.append(PanelAction("sample_proposal", "ارسال نمونه", "success", "ri-upload-cloud-line", requires_file=True))

    if is_staff and project.request_type == "managed_order" and project.status == "submitted":
        actions.append(PanelAction("managed_assign", "تخصیص مدیریت‌شده", "primary", "ri-user-star-line", requires_editor=True))

    if owner and project.status == "editor_selected" and not project.converted_order_id:
        actions.append(PanelAction("convert_to_order", "تبدیل به سفارش", "primary", "ri-arrow-right-circle-line"))

    return actions
