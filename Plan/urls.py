from django.urls import path
from . import views

app_name = 'plan'  # Set the namespace for this app


urlpatterns = [
    path('plan/', views.plan, name = "plan"),
    path('itinerary/', views.itinerary, name = "itinerary"),
    path('locations_list/', views.locations_list, name = "locations_list"),
]