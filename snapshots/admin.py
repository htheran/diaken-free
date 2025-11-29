from django.contrib import admin
from .models import SnapshotHistory


@admin.register(SnapshotHistory)
class SnapshotHistoryAdmin(admin.ModelAdmin):
    list_display = ['snapshot_name', 'host', 'group', 'playbook', 'status', 'created_at', 'expires_at', 'time_until_deletion']
    list_filter = ['status', 'created_at', 'host__environment']
    search_fields = ['snapshot_name', 'host__name', 'description']
    readonly_fields = ['created_at', 'deleted_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Snapshot Information', {
            'fields': ('snapshot_name', 'vcenter_snapshot_id', 'description', 'size_mb')
        }),
        ('Related Objects', {
            'fields': ('host', 'group', 'playbook', 'user')
        }),
        ('Timing', {
            'fields': ('created_at', 'retention_hours', 'expires_at', 'deleted_at')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
    )
