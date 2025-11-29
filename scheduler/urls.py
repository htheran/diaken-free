from django.urls import path
from . import views

urlpatterns = [
    # Scheduling is now integrated in deploy/playbook form
    # path('host/', views.schedule_host_playbook, name='schedule_host_playbook'),  # DEPRECATED
    # path('group/', views.schedule_group_playbook, name='schedule_group_playbook'),  # DEPRECATED
    path('tasks/', views.scheduled_tasks_list, name='scheduled_tasks_list'),
    path('tasks/<int:task_id>/cancel/', views.cancel_scheduled_task, name='cancel_scheduled_task'),
    path('tasks/<int:task_id>/status/', views.get_task_status, name='get_task_status'),
    path('history/', views.scheduled_task_history, name='scheduled_task_history'),
    path('history/<int:history_id>/', views.scheduled_task_history_detail, name='scheduled_task_history_detail'),
    path('history/<int:history_id>/status/', views.get_history_status, name='get_history_status'),
]
