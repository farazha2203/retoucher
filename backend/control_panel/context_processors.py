from .access import panel_capabilities

ROLE_LABELS = {
    "client": "مشتری",
    "editor": "ادیتور",
    "support": "پشتیبان",
    "supervisor": "ناظر",
    "admin": "مدیر",
}


def panel_context(request):
    user = getattr(request, "user", None)
    context = panel_capabilities(user)

    role = context.get("panel_role", "")
    context["panel_role_label"] = ROLE_LABELS.get(role, role or "کاربر")

    return context
