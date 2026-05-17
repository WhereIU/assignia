from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.public_projects, name='public_projects'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('<int:project_pk>/analytics/', views.analytics, name='analytics'),
]
