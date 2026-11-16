from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard"),
    path("learner/", views.learner_dashboard, name="learner_dashboard"),
    path("learning/", views.learning_page, name="learning"),
    path("learning/execute/", views.execute_sql, name="execute_sql"),
    path("learning/saved/", views.saved_query_list, name="saved_query_list"),
    path("learning/saved/new/", views.saved_query_create, name="saved_query_create"),
    path("learning/saved/<int:pk>/", views.saved_query_detail, name="saved_query_detail"),
    path("learning/saved/<int:pk>/edit/", views.saved_query_edit, name="saved_query_edit"),
    path("learning/saved/<int:pk>/delete/", views.saved_query_delete, name="saved_query_delete"),
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
