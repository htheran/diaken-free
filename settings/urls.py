from django.urls import path
from . import views

urlpatterns = [
    # Global settings
    path('global/', views.global_setting_list, name='global_setting_list'),
    path('global/create/', views.global_setting_create, name='global_setting_create'),
    path('global/<int:pk>/edit/', views.global_setting_update, name='global_setting_update'),
    path('global/<int:pk>/delete/', views.global_setting_delete, name='global_setting_delete'),
    path('global/export/', views.export_global_settings, name='export_global_settings'),
    path('global/import/', views.import_global_settings, name='import_global_settings'),
    # Secciones
    path('sections/create/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_update, name='section_update'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),
    # Credenciales
    path('credentials/', views.credential_list, name='credential_list'),
    path('credentials/create/', views.credential_create, name='credential_create'),
    path('credentials/<int:pk>/edit/', views.credential_update, name='credential_update'),
    path('credentials/<int:pk>/delete/', views.credential_delete, name='credential_delete'),
    # Certificados SSL
    path('ssl/', views.ssl_certificate_list, name='ssl_certificate_list'),
    path('ssl/create/', views.ssl_certificate_create, name='ssl_certificate_create'),
    path('ssl/<int:pk>/edit/', views.ssl_certificate_update, name='ssl_certificate_update'),
    path('ssl/<int:pk>/delete/', views.ssl_certificate_delete, name='ssl_certificate_delete'),
    # vCenter
    path('vcenter/', views.vcenter_credential_list, name='vcenter_credential_list'),
    path('vcenter/create/', views.vcenter_credential_create, name='vcenter_credential_create'),
    path('vcenter/<int:pk>/edit/', views.vcenter_credential_update, name='vcenter_credential_update'),
    path('vcenter/<int:pk>/delete/', views.vcenter_credential_delete, name='vcenter_credential_delete'),
    # Ansible Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/upload/', views.template_upload, name='template_upload'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
]
