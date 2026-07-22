from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from accounts.models import EditorProfile
from catalog.models import EditStyle


User = get_user_model()


class AdminUserCreateForm(UserCreationForm):
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=User.Role.choices)
    is_active = forms.BooleanField(required=False, initial=True)
    is_verified = forms.BooleanField(required=False)
    is_staff = forms.BooleanField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_verified",
            "is_staff",
        )

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        if actor is not None and not actor.is_superuser:
            self.fields["role"].choices = [
                item for item in User.Role.choices
                if item[0] != User.Role.ADMIN
            ]
            self.fields["is_staff"].disabled = True

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role == User.Role.ADMIN and not getattr(self.actor, "is_superuser", False):
            raise forms.ValidationError(
                "فقط سوپرادمین می‌تواند مدیر جدید ایجاد کند."
            )
        return role

    def clean_is_staff(self):
        value = self.cleaned_data.get("is_staff", False)
        if value and not getattr(self.actor, "is_superuser", False):
            raise forms.ValidationError(
                "فقط سوپرادمین می‌تواند دسترسی Staff بدهد."
            )
        return value


class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_verified",
            "is_staff",
        )

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        if actor is not None and not actor.is_superuser:
            self.fields["role"].choices = [
                item for item in User.Role.choices
                if item[0] != User.Role.ADMIN
            ]
            self.fields["is_staff"].disabled = True

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role == User.Role.ADMIN and not getattr(self.actor, "is_superuser", False):
            raise forms.ValidationError(
                "فقط سوپرادمین می‌تواند نقش مدیر تنظیم کند."
            )
        return role

    def clean_is_staff(self):
        value = self.cleaned_data.get("is_staff", False)
        if value and not getattr(self.actor, "is_superuser", False):
            raise forms.ValidationError(
                "فقط سوپرادمین می‌تواند دسترسی Staff بدهد."
            )
        return value


class EditorProfileAdminForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=EditStyle.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 8}),
    )

    class Meta:
        model = EditorProfile
        fields = (
            "display_name",
            "bio",
            "level",
            "skills",
            "base_price",
            "average_delivery_hours",
            "is_available",
            "accepts_direct_requests",
            "accepts_public_requests",
            "accepts_sample_challenges",
            "admin_note",
        )
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "base_price": forms.NumberInput(attrs={"class": "form-control"}),
            "average_delivery_hours": forms.NumberInput(attrs={"class": "form-control"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "accepts_direct_requests": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "accepts_public_requests": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "accepts_sample_challenges": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "admin_note": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
