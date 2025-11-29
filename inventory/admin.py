from django.contrib import admin
from .models import Host, Group, Environment
import logging

logger = logging.getLogger(__name__)


class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip', 'environment', 'group', 'operating_system', 'active', 'vcenter_server')
    list_filter = ('active', 'environment', 'group', 'operating_system')
    search_fields = ('name', 'ip', 'description')
    list_editable = ('active',)
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to ensure /etc/hosts is updated.
        """
        super().save_model(request, obj, form, change)
        
        # Force update of /etc/hosts
        try:
            obj.update_etc_hosts()
            logger.info(f'Admin: Updated /etc/hosts after saving {obj.name} (active={obj.active})')
        except Exception as e:
            logger.error(f'Admin: Error updating /etc/hosts for {obj.name}: {e}', exc_info=True)
    
    def delete_model(self, request, obj):
        """
        Override delete_model to ensure /etc/hosts is updated.
        """
        host_name = obj.name
        host_ip = obj.ip
        
        # Delete will call remove_from_etc_hosts() automatically
        super().delete_model(request, obj)
        
        logger.info(f'Admin: Deleted {host_name} ({host_ip}) from inventory and /etc/hosts')
    
    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset for bulk delete to ensure /etc/hosts is updated.
        """
        # Delete each host individually to trigger remove_from_etc_hosts()
        for obj in queryset:
            obj.delete()
        
        logger.info(f'Admin: Bulk deleted {queryset.count()} hosts')


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


# Register models with custom admin
admin.site.register(Host, HostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Environment, EnvironmentAdmin)
