from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('audit/', include('audit.urls')),
]
