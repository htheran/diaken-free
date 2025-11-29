from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Webhook management
    path('', views.webhook_list, name='webhook_list'),
    path('create/', views.webhook_create, name='webhook_create'),
    path('<int:pk>/edit/', views.webhook_edit, name='webhook_edit'),
    path('<int:pk>/delete/', views.webhook_delete, name='webhook_delete'),
    path('<int:pk>/toggle-active/', views.webhook_toggle_active, name='webhook_toggle_active'),
    path('<int:pk>/test/', views.webhook_test, name='webhook_test'),
    path('<int:pk>/configure/', views.webhook_configure, name='webhook_configure'),
    
    # Notification logs
    path('logs/', views.notification_logs, name='notification_logs'),
]
