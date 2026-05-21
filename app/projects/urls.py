from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.available_projects, name='available_projects'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new/', views.project_create, name='project_create'),
    path('project/<str:username>/<str:slug>/', views.project_detail, name='project_detail'),
    path('project/<str:username>/<str:slug>/tasks/', views.project_tasks, name='project_tasks'),
    path('project/<str:username>/<str:slug>/requests/', views.project_requests_content, name='project_requests_content'),
    path('project/<str:username>/<str:slug>/analytics/', views.project_analytics_content, name='project_analytics_content'),
    path('project/<str:username>/<str:slug>/requests/new/', views.request_create_form, name='request_create_form'),
    path('project/<str:username>/<str:slug>/requests/create/', views.request_create_submit, name='request_create_submit'),
    path('project/<str:username>/<str:slug>/join/', views.project_join, name='project_join'),
    path('project/<str:username>/<str:slug>/requests/<int:request_pk>/', views.request_detail, name='request_detail'),
    path('project/<str:username>/<str:slug>/requests/<int:request_pk>/message/', views.request_add_message, name='request_add_message'),
    path('project/<str:username>/<str:slug>/requests/<int:request_pk>/convert/', views.request_convert_to_task, name='request_convert_to_task'),
]