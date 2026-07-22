from __future__ import annotations

from allauth.socialaccount.adapter import (
    DefaultSocialAccountAdapter,
)
from allauth.socialaccount.models import SocialLogin


class RetoucherSocialAccountAdapter(
    DefaultSocialAccountAdapter
):
    """
    Retoucher-specific social authentication rules.

    All newly created social accounts start as regular clients.
    Roles such as editor, support, supervisor and admin can only be
    assigned through the protected administration panel.
    """

    def populate_user(
        self,
        request,
        sociallogin: SocialLogin,
        data: dict,
    ):
        user = super().populate_user(
            request,
            sociallogin,
            data,
        )

        # Never allow a social provider to assign privileged roles.
        if not getattr(user, "pk", None):
            user.role = user.Role.CLIENT
            user.is_staff = False
            user.is_superuser = False

        return user

    def save_user(
        self,
        request,
        sociallogin: SocialLogin,
        form=None,
    ):
        user = super().save_user(
            request,
            sociallogin,
            form,
        )

        # New Google users are regular verified clients.
        if not user.role:
            user.role = user.Role.CLIENT

        user.is_verified = True
        user.is_active = True

        user.save(
            update_fields=[
                "role",
                "is_verified",
                "is_active",
                "updated_at",
            ]
        )

        return user

    def is_open_for_signup(
        self,
        request,
        sociallogin: SocialLogin,
    ) -> bool:
        return True