from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.available_projects, name='available_projects'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new/', views.create_project, name='create_project'),

    path('project/<str:username>/<str:slug>/', views.detail_project, name='detail_project'),
    path('project/<str:username>/<str:slug>/tasks/', views.project_tasks, name='project_tasks'),
    path('project/<str:username>/<str:slug>/join/', views.join_project, name='join_project'),

    path('project/<str:username>/<str:slug>/tab/analytics/', views.project_analytics_tab, name='project_analytics_tab'),
]
