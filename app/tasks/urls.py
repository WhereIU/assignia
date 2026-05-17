from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('take/<int:pk>/', views.take_task, name='take_task'),
    path('<int:task_pk>/comment/', views.add_comment, name='add_comment'),
    path('request/<int:project_pk>/', views.create_request, name='create_request'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('notifications/', views.notifications_list, name='notifications'),
]
