from django.urls import path
from . import views

urlpatterns = [
    path('', views.vm_list, name='vm_list'),
    path('export/', views.export_csv, name='vm_export_csv'),
]
