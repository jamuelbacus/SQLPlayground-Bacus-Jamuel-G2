from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import CustomUser


class AdminUserCreateForm(UserCreationForm):
    """Create a user from the project's own administrator screens."""

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "contact_number",
            "role",
            "is_active",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "Username", "autocomplete": "off"}
            ),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "contact_number": forms.TextInput(
                attrs={"placeholder": "+639171234567", "autocomplete": "tel"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].initial = True
        for field in self.fields.values():
            if field.widget.input_type != "checkbox":
                field.widget.attrs.setdefault("class", "form-input")


class AdminUserEditForm(forms.ModelForm):
    """Update account details, role, and active status."""

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "contact_number",
            "role",
            "is_active",
        )
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "off"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "contact_number": forms.TextInput(
                attrs={"placeholder": "+639171234567", "autocomplete": "tel"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.widget.input_type != "checkbox":
                field.widget.attrs.setdefault("class", "form-input")
