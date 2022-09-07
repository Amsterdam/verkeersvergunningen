from django.urls import path

from . import views

urlpatterns = [
    path("get_permits/", views.PermitView.as_view(), name='taxi_permit'),
]
