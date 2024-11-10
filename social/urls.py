# social/urls.py

from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('rate/', views.rate_location, name='rate_location'),
    path('add_location/', views.add_location, name='add_location'),
]
