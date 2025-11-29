from django.contrib import admin
from .models import WindowsCredential

@admin.register(WindowsCredential)
class WindowsCredentialAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'domain', 'auth_type', 'use_https', 'created_at')
    list_filter = ('auth_type', 'use_https', 'created_at')
    search_fields = ('name', 'username', 'domain', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Credentials', {
            'fields': ('username', 'password', 'domain')
        }),
        ('WinRM Configuration', {
            'fields': ('auth_type', 'use_https')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register your models here.
