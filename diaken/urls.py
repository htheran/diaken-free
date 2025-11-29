"""
URL configuration for diaken project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
import os

def view_notice(request):
    """Serve the NOTICE file"""
    notice_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'NOTICE')
    with open(notice_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/plain; charset=utf-8')

urlpatterns = [
    path('notice/', view_notice, name='view_notice'),
    path('deploy/', include('deploy.urls')),
    path('admin/', admin.site.urls),
    path('', include('login.urls')),
    path('settings/', include('settings.urls')),
    path('inventory/', include('inventory.urls')),
    path('history/', include('history.urls')),
    path('playbooks/', include('playbooks.urls')),
    path('scheduler/', include('scheduler.urls')),
    path('users/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('snapshots/', include('snapshots.urls')),
    path('scripts/', include('scripts.urls')),
    path('notifications/', include('notifications.urls')),
    path('addressing/', include('addressing.urls')),
]
