from django.db.models import Q


MANAGEMENT_ROLES = {"admin", "support", "supervisor"}
FINANCE_ROLES = {"admin", "support"}


def _role(user):
    return getattr(user, "role", "") or ""


def _is_authenticated(user):
    return bool(user and getattr(user, "is_authenticated", False))


def is_management(user):
    return bool(
        _is_authenticated(user)
        and (
            getattr(user, "is_staff", False)
            or _role(user) in MANAGEMENT_ROLES
        )
    )


def is_finance_manager(user):
    return bool(
        _is_authenticated(user)
        and (
            getattr(user, "is_staff", False)
            or _role(user) in FINANCE_ROLES
        )
    )


def _editor_profile_id(user):
    if not _is_authenticated(user):
        return None

    try:
        return user.editor_profile_id
    except AttributeError:
        profile = getattr(user, "editor_profile", None)
        return getattr(profile, "pk", None)


def visible_conversations(user, queryset):
    if not _is_authenticated(user):
        return queryset.none()

    if is_management(user):
        return queryset

    filters = (
        Q(participants=user)
        | Q(created_by=user)
        | Q(order__client=user)
        | Q(order__editor=user)
        | Q(project_request__client=user)
        | Q(project_request__target_editor__user=user)
    )

    return queryset.filter(filters).distinct()


def can_access_conversation(user, conversation):
    if not _is_authenticated(user):
        return False

    if is_management(user):
        return True

    if conversation.created_by_id == user.pk:
        return True

    if conversation.participants.filter(pk=user.pk).exists():
        return True

    if conversation.order_id:
        if user.pk in {
            conversation.order.client_id,
            getattr(conversation.order, "editor_id", None),
        }:
            return True

    if conversation.project_request_id:
        project = conversation.project_request
        target_editor_user_id = getattr(
            getattr(project, "target_editor", None),
            "user_id",
            None,
        )

        if user.pk in {
            project.client_id,
            target_editor_user_id,
        }:
            return True

    return False


def visible_files(user, queryset):
    if not _is_authenticated(user):
        return queryset.none()

    if is_management(user):
        return queryset

    filters = (
        Q(uploaded_by=user)
        | Q(order__client=user)
        | Q(order__editor=user)
        | Q(project_request__client=user)
        | Q(project_request__target_editor__user=user)
    )

    return queryset.filter(filters).distinct()
