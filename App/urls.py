from django.urls import path, include

from App import views

urlpatterns = [
    path('', views.auth),
]