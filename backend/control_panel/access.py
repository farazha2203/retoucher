from django.db.models import Q

ORDER_STAFF_ROLES = {"admin", "support", "supervisor"}
FINANCE_ADMIN_ROLES = {"admin", "support"}


def role(user):
    return getattr(user, "role", "") or ""


def authenticated(user):
    return bool(user and getattr(user, "is_authenticated", False))


def is_order_staff(user):
    return bool(
        authenticated(user)
        and (getattr(user, "is_staff", False) or role(user) in ORDER_STAFF_ROLES)
    )


def is_finance_admin(user):
    return bool(
        authenticated(user)
        and (getattr(user, "is_staff", False) or role(user) in FINANCE_ADMIN_ROLES)
    )


def is_project_staff(user):
    # Project admin/review endpoints use DRF IsAdminUser, therefore is_staff.
    return bool(authenticated(user) and getattr(user, "is_staff", False))


def visible_orders(user, queryset):
    if not authenticated(user):
        return queryset.none()
    if is_order_staff(user):
        return queryset
    return queryset.filter(Q(client=user) | Q(editor=user))


def can_view_order(user, order):
    return bool(
        is_order_staff(user)
        or (
            authenticated(user)
            and user.pk in {order.client_id, getattr(order, "editor_id", None)}
        )
    )


def visible_projects(user, queryset):
    if not authenticated(user):
        return queryset.none()
    if is_project_staff(user):
        return queryset

    editor_profile = getattr(user, "editor_profile", None)
    if editor_profile is None:
        return queryset.filter(client=user)

    return queryset.filter(
        Q(client=user)
        | Q(target_editor=editor_profile)
        | Q(
            request_type="public_quote",
            status="open_for_quotes",
            edit_style__in=editor_profile.skills.all(),
        )
        | Q(
            request_type="sample_challenge",
            status="open_for_samples",
            edit_style__in=editor_profile.skills.all(),
        )
    ).distinct()


def can_view_project(user, project):
    if is_project_staff(user):
        return True
    if not authenticated(user):
        return False
    if project.client_id == user.pk:
        return True

    editor_profile = getattr(user, "editor_profile", None)
    if editor_profile is None:
        return False
    if project.target_editor_id == editor_profile.pk:
        return True
    if (
        project.request_type == "public_quote"
        and project.status == "open_for_quotes"
        and editor_profile.skills.filter(pk=project.edit_style_id).exists()
    ):
        return True
    if (
        project.request_type == "sample_challenge"
        and project.status == "open_for_samples"
        and editor_profile.skills.filter(pk=project.edit_style_id).exists()
    ):
        return True
    return False


def visible_project_proposals(user, project, queryset):
    """Mirror ProjectRequestDetailSerializer.get_proposals exactly."""
    if not authenticated(user):
        return queryset.none()
    if is_project_staff(user):
        return queryset
    if project.client_id == user.pk:
        from projects.models import ProjectProposal, ProjectRequest
        return queryset.filter(
            Q(is_visible_to_client=True)
            | Q(status=ProjectProposal.Status.ACCEPTED_BY_CLIENT)
            | Q(
                project_request__request_type=ProjectRequest.RequestType.PUBLIC_QUOTE,
                status=ProjectProposal.Status.SUBMITTED,
            )
            | Q(
                project_request__request_type=ProjectRequest.RequestType.SAMPLE_CHALLENGE,
                status=ProjectProposal.Status.APPROVED,
            )
        )

    editor_profile = getattr(user, "editor_profile", None)
    if editor_profile:
        return queryset.filter(editor=editor_profile)
    return queryset.none()


def visible_wallets(user, queryset):
    if not authenticated(user):
        return queryset.none()
    return queryset if is_finance_admin(user) else queryset.filter(user=user)


def visible_transactions(user, queryset):
    if not authenticated(user):
        return queryset.none()
    return queryset if is_finance_admin(user) else queryset.filter(wallet__user=user)


def visible_payment_requests(user, queryset):
    if not authenticated(user):
        return queryset.none()
    return queryset if is_finance_admin(user) else queryset.filter(user=user)


def visible_refunds(user, queryset):
    if not authenticated(user):
        return queryset.none()
    return queryset if getattr(user, "is_staff", False) else queryset.filter(order__client=user)


def panel_capabilities(user):
    current_role = role(user)
    return {
        "panel_role": current_role,
        "panel_is_client": current_role == "client",
        "panel_is_editor": current_role == "editor",
        "panel_is_support": current_role == "support",
        "panel_is_supervisor": current_role == "supervisor",
        "panel_is_admin": current_role == "admin",
        "panel_is_order_staff": is_order_staff(user),
        "panel_is_management": is_order_staff(user),
        "panel_is_project_staff": is_project_staff(user),
        "panel_can_view_finance": authenticated(user),
        "panel_can_manage_finance": is_finance_admin(user),
        "panel_can_withdraw": current_role == "editor",
        "panel_can_request_refund": current_role == "client",
        "panel_can_manage_users": bool(
            authenticated(user) and (getattr(user, "is_staff", False) or current_role == "admin")
        ),
        "panel_can_view_audit": is_order_staff(user),
        "panel_can_view_backend": bool(
            authenticated(user) and (getattr(user, "is_staff", False) or current_role == "admin")
        ),
        "panel_can_access_system_admin": bool(
            authenticated(user) and getattr(user, "is_staff", False)
        ),
    }
