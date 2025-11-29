from django.contrib import admin
from .models import Script


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ['name', 'os_family', 'target_type', 'active', 'created_at', 'updated_at']
    list_filter = ['os_family', 'target_type', 'active']
    search_fields = ['name', 'description']
    readonly_fields = ['file_path', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'active')
        }),
        ('Configuration', {
            'fields': ('target_type', 'os_family')
        }),
        ('File Information', {
            'fields': ('file_path',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
