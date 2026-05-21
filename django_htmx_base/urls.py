from django.urls import path
from . import views

app_name = "base"

urlpatterns = [
    path("ping/", views.ping, name="ping"),
]
