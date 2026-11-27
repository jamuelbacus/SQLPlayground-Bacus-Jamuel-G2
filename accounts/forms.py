from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image

from .models import CustomUser

MAX_PROFILE_PHOTO_BYTES = 2 * 1024 * 1024
MAX_PROFILE_PHOTO_DIMENSION = 2000


def validate_profile_photo(photo):
    """Apply the application's explicit profile-photo limits to new uploads."""
    if not isinstance(photo, UploadedFile):
        return photo
    if photo.size > MAX_PROFILE_PHOTO_BYTES:
        raise ValidationError("Profile photo must be 2 MB or smaller.")
    try:
        with Image.open(photo) as image:
            width, height = image.size
    finally:
        photo.seek(0)
    if max(width, height) > MAX_PROFILE_PHOTO_DIMENSION:
        raise ValidationError("Profile photo dimensions must not exceed 2000 pixels.")
    return photo


class SignUpForm(UserCreationForm):
    """Registration form for learners.

    Role is deliberately not a form field. Self-registration always creates a
    Learner account; Administrator accounts are created by the project team
    through createsuperuser or the Manage Users screens.
    """

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First name",
                "autocomplete": "given-name",
                "autofocus": True,
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Last name", "autocomplete": "family-name"}
        ),
    )
    email = forms.EmailField(
        label="Email address",
        required=True,
        widget=forms.EmailInput(
            attrs={"placeholder": "you@example.com", "autocomplete": "email"}
        ),
    )

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.fields["username"]
        username.widget.attrs.update(
            {"autocomplete": "username", "placeholder": "Choose a username"}
        )
        username.widget.attrs.pop("autofocus", None)
        username.help_text = (
            "Choose a username you can use to log in. Letters, digits and "
            "@/./+/-/_ only."
        )
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password1"].widget.attrs["aria-describedby"] = "password-rules"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].label = "Confirm password"
        for field in self.fields.values():
            if field.widget.input_type != "checkbox":
                field.widget.attrs.setdefault("class", "form-input")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"]
        user.role = CustomUser.Role.LEARNER
        if commit:
            user.save()
        return user


class AccountLoginForm(AuthenticationForm):
    """Login form with a single, clear invalid-credentials message."""

    error_messages = {
        "invalid_login": (
            "Invalid username or password. Please check your credentials "
            "and try again."
        ),
        "inactive": "This account is inactive.",
    }
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username or email"
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "placeholder": "Username or email address",
            }
        )
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"
        for field in self.fields.values():
            if field.widget.input_type != "checkbox":
                field.widget.attrs.setdefault("class", "form-input")

    def clean(self):
        identifier = self.cleaned_data.get("username")
        if identifier:
            is_username = CustomUser.objects.filter(username=identifier).exists()
            if not is_username:
                matches = CustomUser.objects.filter(email__iexact=identifier)
                if matches.count() == 1:
                    self.cleaned_data["username"] = matches.first().username
        return super().clean()


class ProfileForm(forms.ModelForm):
    """Form used by a logged-in user to update their own profile."""

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "contact_number", "profile_photo")
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "contact_number": forms.TextInput(
                attrs={"placeholder": "+639171234567", "autocomplete": "tel"}
            ),
            "profile_photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {
            "profile_photo": "Profile photo",
            "contact_number": "Contact number",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        for name, field in self.fields.items():
            if name != "profile_photo":
                field.widget.attrs.setdefault("class", "form-input")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        duplicates = CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_profile_photo(self):
        return validate_profile_photo(self.cleaned_data["profile_photo"])


class AccountPasswordChangeForm(PasswordChangeForm):
    """Password change form styled like the project's other account forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update(
            {"autocomplete": "current-password", "autofocus": True}
        )
        self.fields["new_password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].label = "Confirm new password"
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-input")
