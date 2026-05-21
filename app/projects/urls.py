from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.available_projects, name='available_projects'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new/', views.project_create, name='project_create'),
    path('custom/<str:username>/<str:slug>/', views.project_detail, name='project_detail'),
    path('custom/<str:username>/<str:slug>/tasks/', views.project_tasks, name='project_tasks'),
    path('custom/<str:username>/<str:slug>/requests/', views.project_requests_content, name='project_requests_content'),
    path('custom/<str:username>/<str:slug>/analytics/', views.project_analytics_content, name='project_analytics_content'),
    path('custom/<str:username>/<str:slug>/requests/new/', views.project_request_create, name='project_request_create'),
    path('custom/<str:username>/<str:slug>/join/', views.project_join, name='project_join'),
]