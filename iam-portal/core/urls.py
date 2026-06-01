from django.urls import path
from core import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('launcher/', views.launcher, name='launcher'),
    path('launch/<str:app_id>/', views.app_launch, name='app_launch'),
]
