from django.urls import path

from . import views

urlpatterns = [
    path("ontheffingen/", views.OntheffingenBSNView.as_view(), name='taxi_ontheffingen_bsn'),
    path("ontheffingen/<str:ontheffingsnummer>/", views.OntheffingDetailView.as_view(), name='taxi_ontheffing_details'),
]
