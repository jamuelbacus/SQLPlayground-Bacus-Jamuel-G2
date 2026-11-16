from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard"),
    path("learner/", views.learner_dashboard, name="learner_dashboard"),
    path("administrator/", views.administrator_dashboard, name="administrator_dashboard"),
    path("administrator/users/", views.manage_users, name="manage_users"),
    path("administrator/users/new/", views.user_create, name="user_create"),
    path("administrator/users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path(
        "administrator/users/<int:pk>/password/",
        views.user_password,
        name="user_password",
    ),
    path("administrator/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
]
