from django.urls import path
from . import views

urlpatterns = [
    path('', views.playbook_list, name='playbook_list'),
    path('host/', views.playbook_list_host, name='playbook_list_host'),
    path('group/', views.playbook_list_group, name='playbook_list_group'),
    path('create/', views.playbook_create, name='playbook_create'),
    path('upload/', views.playbook_upload, name='playbook_upload'),
    path('<int:pk>/view/', views.playbook_view, name='playbook_view'),
    path('<int:pk>/edit/', views.playbook_edit, name='playbook_edit'),
    path('<int:pk>/download/', views.playbook_download, name='playbook_download'),
    path('<int:pk>/delete/', views.playbook_delete, name='playbook_delete'),
]
