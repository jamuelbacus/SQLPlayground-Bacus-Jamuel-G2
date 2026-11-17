from django.urls import path

from . import views

urlpatterns = [
    path("", views.lesson_index, name="lesson_index"),
    path("<slug:slug>/check/", views.lesson_check, name="lesson_check"),
    path("<slug:slug>/", views.lesson_detail, name="lesson_detail"),
]
