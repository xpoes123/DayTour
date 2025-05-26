from django.urls import path
from . import views

app_name = 'plan'


urlpatterns = [
    path('plan/', views.plan, name = "plan"),
    path('itinerary/<int:page_num>/', views.itinerary_page, name='itinerary_page'),
    path('locations_list/', views.locations_list, name = "locations_list"),
]