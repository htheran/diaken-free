from django.urls import path
from . import views
from . import views_group
from . import views_windows
from . import views_playbook
from . import views_playbook_windows
from . import views_task_status
from . import views_sse
from . import views_test
from . import ajax

app_name = 'deploy'

urlpatterns = [
    # Deploy VM from vCenter
    path('', views.deploy_index, name='deploy_index'),
    path('vm/', views.deploy_vm, name='deploy_vm'),
    path('clear-auto-open/', views.clear_auto_open, name='clear_auto_open'),
    
    # Deploy Windows VM
    path('windows/', views_windows.deploy_windows_vm, name='deploy_windows_vm'),
    path('windows/run/', views_windows.deploy_windows_vm_run, name='deploy_windows_vm_run'),
    
    # Execute playbook on existing host
    path('playbook/', views_playbook.deploy_playbook, name='deploy_playbook'),
    path('playbook/execute/', views_playbook.execute_playbook, name='execute_playbook'),
    path('playbook/get-playbooks/', views_playbook.get_playbooks, name='get_playbooks'),
    
    # Execute playbook on group
    path('group/', views_group.execute_group_playbook, name='execute_group_playbook'),
    path('group/execute/', views_group.execute_group_playbook_run, name='execute_group_playbook_run'),
    
    # Execute Windows playbook
    path('playbook/windows/', views_playbook_windows.deploy_playbook_windows, name='deploy_playbook_windows'),
    
    # Task status API
    path('task-status/<str:task_id>/', views_task_status.task_status, name='task_status'),
    path('history-status/<int:history_id>/', views_task_status.history_status, name='history_status'),
    
    # SSE (Server-Sent Events) for real-time updates
    path('stream/<int:history_id>/', views_sse.deployment_stream, name='deployment_stream'),
    path('test-sse/', views_test.test_sse, name='test_sse'),
    path('playbook/windows/execute/', views_playbook_windows.execute_playbook_windows, name='execute_playbook_windows'),
    
    # AJAX endpoints
    path('ajax/get_datacenters/', ajax.get_datacenters, name='ajax_get_datacenters'),
    path('ajax/get_clusters/', ajax.get_clusters, name='ajax_get_clusters'),
    path('ajax/get_resource_pools/', ajax.get_resource_pools, name='ajax_get_resource_pools'),
    path('ajax/get_templates/', ajax.get_templates, name='ajax_get_templates'),
    path('ajax/get_datastores/', ajax.get_datastores, name='ajax_get_datastores'),
    path('ajax/get_networks/', ajax.get_networks, name='ajax_get_networks'),
    path('ajax/get_folders/', ajax.get_folders, name='ajax_get_folders'),
    path('ajax/get_groups/', ajax.get_groups, name='ajax_get_groups'),
    path('ajax/get_hosts/', ajax.get_hosts, name='ajax_get_hosts'),
    path('ajax/task-progress/<str:task_id>/', ajax.get_task_progress, name='ajax_get_task_progress'),
]
