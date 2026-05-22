from django.urls import path

from . import views

app_name = 'tasks'


urlpatterns = [
    path('task/<str:username>/<str:slug>/new/', views.task_create, name='task_create'),
    path('task/<int:task_pk>/detail/', views.task_detail, name='task_detail'),
    path('task/<int:task_pk>/take', views.task_take, name='task_take'),
    path('task/<int:task_pk>/comment', views.add_comment, name='add_comment'),
    path('request/<str:username>/<str:slug>/', views.create_request, name='create_request'),
]
