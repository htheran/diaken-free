from django.urls import path
from . import views

app_name = 'history'

urlpatterns = [
    path('', views.history_list, name='history_list'),
    path('<int:pk>/', views.history_detail, name='history_detail'),
    path('<int:pk>/status/', views.check_task_status, name='check_task_status'),
    path('cleanup/', views.cleanup_stuck_deployments_view, name='cleanup_stuck_deployments'),
]
