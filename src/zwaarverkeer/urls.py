from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path("has_permit/", views.HasPermitView.as_view(), name='zwaarverkeer_has_permit'),
]
