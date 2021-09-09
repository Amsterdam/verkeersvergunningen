from django.urls import path

from . import views

urlpatterns = [
    path("has_permit/", views.zwaar_verkeer, name='zwaarverkeer_check_by_number_plate'),
]
