# social/urls.py

from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('rate/', views.rate_location, name='rate_location'),
]
