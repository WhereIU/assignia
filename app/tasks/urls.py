from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('take/<int:pk>/', views.take_task, name='take_task'),
    path('<int:task_pk>/comment/', views.add_comment, name='add_comment'),
    path('request/<int:project_pk>/', views.create_request, name='create_request'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('project/<str:username>/<str:slug>/tasks/<int:task_pk>/', views.task_detail, name='task_detail'),
    path('<str:username>/<str:slug>/tasks/new/', views.task_create, name='task_create'),
]