import ckeditor_uploader
from django.contrib import admin
from django.urls import path, include, re_path

from journeys.admin import admin_site

urlpatterns = [
    path('', include('journeys.urls')),
    path('admin/', admin_site.urls),
    re_path(r'^ckeditor/',include('ckeditor_uploader.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
