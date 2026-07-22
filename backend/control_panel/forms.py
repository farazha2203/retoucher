from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from accounts.models import EditorProfile
from catalog.models import EditPackage, EditStyle
from projects.models import ProjectRequest


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



class PanelOrderCreateForm(forms.Form):
    title = forms.CharField(
        label="عنوان سفارش",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "مثلاً روتوش حرفه‌ای تصاویر مراسم",
            }
        ),
    )
    description = forms.CharField(
        label="شرح کامل سفارش",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 7,
                "placeholder": "توضیحات، جزئیات و انتظارات خود را بنویسید.",
            }
        ),
    )
    deadline = forms.DateTimeField(
        label="مهلت ترجیحی",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"class": "form-control", "type": "datetime-local"},
        ),
    )


class PanelProjectCreateForm(forms.Form):
    request_type = forms.ChoiceField(
        label="نوع درخواست",
        choices=ProjectRequest.RequestType.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    title = forms.CharField(
        label="عنوان پروژه",
        max_length=180,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "عنوان کوتاه و شفاف پروژه",
            }
        ),
    )
    description = forms.CharField(
        label="شرح پروژه",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 7,
                "placeholder": "جزئیات کار، سبک موردنظر و خروجی مطلوب",
            }
        ),
    )
    edit_style = forms.ModelChoiceField(
        label="سبک ویرایش",
        queryset=EditStyle.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    package = forms.ModelChoiceField(
        label="بسته خدمات",
        queryset=EditPackage.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    target_editor = forms.ModelChoiceField(
        label="ادیتور هدف",
        queryset=EditorProfile.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    budget_min = forms.IntegerField(
        label="حداقل بودجه",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    budget_max = forms.IntegerField(
        label="حداکثر بودجه",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    preferred_deadline = forms.DateTimeField(
        label="مهلت ترجیحی",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"class": "form-control", "type": "datetime-local"},
        ),
    )
    client_note = forms.CharField(
        label="یادداشت مشتری",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["edit_style"].queryset = (
            EditStyle.objects.filter(is_active=True)
            .select_related("category")
            .order_by("category__sort_order", "sort_order", "title")
        )
        self.fields["package"].queryset = (
            EditPackage.objects.filter(is_active=True, style__is_active=True)
            .select_related("style")
            .order_by("style__title", "sort_order", "price")
        )
        self.fields["target_editor"].queryset = (
            EditorProfile.objects.filter(
                is_available=True,
                accepts_direct_requests=True,
                user__is_active=True,
            )
            .select_related("user")
            .order_by("-rating_average", "display_name")
        )

    def clean(self):
        cleaned = super().clean()
        request_type = cleaned.get("request_type")
        target_editor = cleaned.get("target_editor")
        edit_style = cleaned.get("edit_style")
        package = cleaned.get("package")

        if (
            request_type == ProjectRequest.RequestType.DIRECT_EDITOR
            and target_editor is None
        ):
            self.add_error(
                "target_editor",
                "برای درخواست مستقیم باید ادیتور انتخاب شود.",
            )

        if package and edit_style and package.style_id != edit_style.id:
            self.add_error(
                "package",
                "بسته انتخابی باید متعلق به سبک انتخاب‌شده باشد.",
            )

        return cleaned
