from django.shortcuts import render


def custom_404(request, exception):
    """Render the project's not-found page."""
    return render(request, "404.html", status=404)


def custom_500(request):
    """Render the project's server-error page without request internals."""
    return render(request, "500.html", status=500)
