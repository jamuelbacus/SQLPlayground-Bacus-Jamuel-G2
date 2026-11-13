from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import SignUpForm


def home(request):
    """Public landing page for SQL Playground."""
    return render(request, "home.html")


def signup(request):
    """Create a learner account, then ask the user to log in."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your account was created successfully.",
            )
            return redirect("home")
        messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})
