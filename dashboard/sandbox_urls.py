from django.urls import path

from . import views

urlpatterns = [
    path("", views.sandbox, name="sandbox"),
    path("execute/", views.sandbox_execute, name="sandbox_execute"),
    path("history/", views.query_history_list, name="query_history_list"),
    path("saved/", views.saved_query_list, name="saved_query_list"),
    path("saved/new/", views.saved_query_create, name="saved_query_create"),
    path(
        "saved/<int:pk>/",
        views.saved_query_detail,
        name="saved_query_detail",
    ),
    path(
        "saved/<int:pk>/edit/",
        views.saved_query_edit,
        name="saved_query_edit",
    ),
    path(
        "saved/<int:pk>/delete/",
        views.saved_query_delete,
        name="saved_query_delete",
    ),
]
