from django.urls import path

from . import views

urlpatterns = [
    path("ontheffingen/", views.OntheffingView.as_view(), name='taxi_ontheffing'),
    path("handhavingen/<str:ontheffingsnummer>/",
         views.HandhavingView.as_view(), name='taxi_handhaving'),
]
