from django import forms

from .models import Conversation, ManagedFile


class ConversationCreateForm(forms.ModelForm):
    participant_ids = forms.CharField(required=False)

    class Meta:
        model = Conversation
        fields = ("title", "kind", "order", "project_request")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "order": forms.Select(attrs={"class": "form-select"}),
            "project_request": forms.Select(attrs={"class": "form-select"}),
        }


class ManagedFileUploadForm(forms.ModelForm):
    class Meta:
        model = ManagedFile
        fields = ("file", "title", "category", "order", "project_request", "description", "is_private")
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "order": forms.Select(attrs={"class": "form-select"}),
            "project_request": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_private": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
