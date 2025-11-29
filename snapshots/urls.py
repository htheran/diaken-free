from django.urls import path
from . import views

urlpatterns = [
    path('', views.snapshot_history, name='snapshot_history'),
    path('<int:pk>/', views.snapshot_detail, name='snapshot_detail'),
    path('<int:pk>/delete/', views.delete_snapshot, name='delete_snapshot'),
]
