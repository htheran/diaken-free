from django.contrib import admin
from .models import ScheduledTask, ScheduledTaskHistory

@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'task_type', 'get_target_display', 'playbook', 'scheduled_datetime', 'status', 'created_by']
    list_filter = ['status', 'task_type', 'scheduled_datetime']
    search_fields = ['name', 'host__name', 'group__name', 'playbook__name']
    readonly_fields = ['created_at', 'updated_at', 'execution_started_at', 'execution_completed_at']

@admin.register(ScheduledTaskHistory)
class ScheduledTaskHistoryAdmin(admin.ModelAdmin):
    list_display = ['scheduled_task', 'task_type', 'target_name', 'playbook_name', 'executed_at', 'status']
    list_filter = ['status', 'task_type', 'executed_at']
    search_fields = ['target_name', 'playbook_name', 'scheduled_task__name']
    readonly_fields = ['executed_at']
