from django.urls import path
from . import views

urlpatterns = [
    path('environments/', views.environment_list, name='environment_list'),
    path('environments/create/', views.environment_create, name='environment_create'),
    path('environments/<int:pk>/', views.environment_detail, name='environment_detail'),
    path('environments/<int:pk>/edit/', views.environment_update, name='environment_update'),
    path('environments/<int:pk>/delete/', views.environment_delete, name='environment_delete'),

    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/edit/', views.group_update, name='group_update'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),

    path('hosts/', views.host_list, name='host_list'),
    path('hosts/create/', views.host_create, name='host_create'),
    path('hosts/<int:pk>/', views.host_detail, name='host_detail'),
    path('hosts/<int:pk>/edit/', views.host_update, name='host_update'),
    path('hosts/<int:pk>/delete/', views.host_delete, name='host_delete'),
]
