"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from django.contrib import admin

# dev
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('', include('users.urls', namespace='users')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('tasks/', include('project_tasks.urls', namespace='project_tasks')),
    path('requests/', include('project_requests.urls', namespace='project_requests')),
    path('directions/', include('project_directions.urls', namespace='project_directions')),
    path('teams/', include('project_teams.urls', namespace='project_teams')),
    path('members/', include('project_members.urls', namespace='project_members')),
    path('analytics/', include('project_analytics.urls', namespace='project_analytics'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #dev
