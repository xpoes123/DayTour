from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('home.urls', 'home'), namespace='home')),
    path('', include(('authuser.urls', 'authuser'), namespace='authuser')),
    path('', include(('plan.urls', 'plan'), namespace='plan')),
    path('blog/', include('blog.urls', namespace='blog')),  # Ensure namespace is included

]
