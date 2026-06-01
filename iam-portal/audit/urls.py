from django.urls import path
from audit import views

urlpatterns = [
    path('', views.audit_dashboard, name='audit_dashboard'),
    path('export/', views.export_csv, name='audit_export'),
]
