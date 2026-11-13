from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard"),
    path("learner/", views.learner_dashboard, name="learner_dashboard"),
    path("administrator/", views.administrator_dashboard, name="administrator_dashboard"),
]
