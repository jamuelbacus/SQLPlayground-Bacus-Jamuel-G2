from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import CustomUser
from lessons.engine import MAX_SQL_LENGTH, QueryError, validate_read_only_sql

from .models import SavedQuery


class AdminUserCreateForm(UserCreationForm):
    """Create a user from the project's own administrator screens."""

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
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
            "role",
            "is_active",
        )
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "off"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.widget.input_type != "checkbox":
                field.widget.attrs.setdefault("class", "form-input")


class SavedQueryForm(forms.ModelForm):
    """Create or edit a learner's saved query with server-side validation."""

    class Meta:
        model = SavedQuery
        fields = ("title", "sql")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "sql": forms.Textarea(attrs={"class": "sql-editor", "rows": 12}),
        }

    def __init__(self, data=None, *, user, instance=None):
        super().__init__(data=data, instance=instance)
        self.user = user

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        duplicates = SavedQuery.objects.filter(user=self.user, title__iexact=title)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("You already have a saved query with this title.")
        return title

    def clean_sql(self):
        sql = self.cleaned_data["sql"].strip()
        try:
            validate_read_only_sql(sql)
        except QueryError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return sql

    def save(self, commit=True):
        saved_query = super().save(commit=False)
        saved_query.user = self.user
        if commit:
            saved_query.save()
        return saved_query


class SqlSubmissionForm(forms.Form):
    """Validate SQL typed into the sandbox or a lesson editor."""

    sql = forms.CharField(
        strip=True,
        max_length=MAX_SQL_LENGTH,
        widget=forms.Textarea(
            attrs={"class": "sql-editor", "rows": 12, "spellcheck": "false"}
        ),
    )

    def clean_sql(self):
        sql = self.cleaned_data["sql"]
        try:
            validate_read_only_sql(sql)
        except QueryError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return sql
