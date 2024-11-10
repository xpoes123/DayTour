# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('user/<int:user_id>', views.user_blogs, name='user_blogs'),  # Adjusted to 'user' instead of 'profile'
    path('detail/<int:blog_id>/', views.blog_detail, name='blog_detail'),  # Simplified for clarity
    path('create_post/', views.create_post, name='create_post'),
    path('get_location_ids/<int:itinerary_id>/', views.get_location_ids, name='get_location_ids'),

    path('', views.blog, name='blog'),  # Main blog view
]
