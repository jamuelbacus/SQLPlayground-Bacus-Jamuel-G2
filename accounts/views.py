from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    AccountLoginForm,
    AccountPasswordChangeForm,
    ProfileForm,
    SignUpForm,
)


def home(request):
    """Public landing page for SQL Playground."""
    return render(request, "home.html")


def signup(request):
    """Create a learner account, then ask the user to log in."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your account was created successfully. Please log in.",
            )
            return redirect("login")
        messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


class AccountLoginView(LoginView):
    """Log in with a username or email address and a password."""

    template_name = "accounts/login.html"
    authentication_form = AccountLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(0)
        return response


class AccountLogoutView(LogoutView):
    """End the current session. Logout is POST-only for safety."""

    next_page = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out.")
        return super().post(request, *args, **kwargs)


@login_required
def profile(request):
    """Show the logged-in user's own profile."""
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):
    """Update the logged-in user's own profile."""
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def password_change(request):
    """Change the logged-in user's own password."""
    if request.method == "POST":
        form = AccountPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was changed successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AccountPasswordChangeForm(request.user)

    return render(request, "accounts/password_change.html", {"form": form})
