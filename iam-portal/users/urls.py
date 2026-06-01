from django.urls import path
from users import views

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('creer/', views.user_create, name='user_create'),
    path('<str:user_id>/modifier/', views.user_edit, name='user_edit'),
    path('<str:user_id>/supprimer/', views.user_delete, name='user_delete'),
]
