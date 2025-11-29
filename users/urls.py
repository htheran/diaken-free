from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('create/', views.user_create, name='user_create'),
    path('<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('<int:user_id>/delete/', views.user_delete, name='user_delete'),
]
