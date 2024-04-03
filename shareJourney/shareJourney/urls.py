from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('journeys.urls')),
    path('admin/', admin.site.urls),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
