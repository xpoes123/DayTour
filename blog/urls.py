# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'  # This namespaces all URLs under 'blog'

urlpatterns = [
    path('profile/<int:user_id>/blogs/', views.user_blogs, name='user_blogs'),
    path('<int:blog_id>/', views.blog_detail, name='blog_detail'),
    path('create_post/', views.create_post, name='create_post'),
    path('', views.blog, name='blog'),  # The main blog view, now properly named
]
