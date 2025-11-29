from django.urls import path
from . import views

urlpatterns = [
    path('', views.script_list, name='script_list'),
    path('create/', views.script_create, name='script_create'),
    path('upload/', views.script_upload, name='script_upload'),
    path('<int:pk>/edit/', views.script_edit, name='script_edit'),
    path('<int:pk>/view/', views.script_view, name='script_view'),
    path('<int:pk>/download/', views.script_download, name='script_download'),
    path('<int:pk>/delete/', views.script_delete, name='script_delete'),
    path('<int:pk>/toggle-active/', views.script_toggle_active, name='script_toggle_active'),
    path('get-scripts/', views.get_scripts_ajax, name='get_scripts_ajax'),
]
