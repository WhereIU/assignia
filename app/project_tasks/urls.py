from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('tab/<str:username>/<str:slug>/', views.tasks_tab, name='tasks_tab'),

    path('new/<str:username>/<str:slug>/create/', views.task_create, name='task_create'),
    path('task/<int:task_pk>/', views.task_detail, name='task_detail'),
    path('task/<int:task_pk>/take/', views.task_take, name='task_take'),
    path('task/<int:task_pk>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:task_pk>/delete/confirm/', views.task_delete_confirm, name='task_delete_confirm'),
    path('task/<int:task_pk>/assignees/add/', views.assignee_add, name='assignee_add'),
    path('task/<int:task_pk>/assignees/remove/', views.assignee_remove, name='assignee_remove'),
    path('task/<int:task_pk>/directions/add/', views.direction_add_to_task, name='direction_add_to_task'),
    path('task/<int:task_pk>/directions/remove/', views.direction_remove_from_task, name='direction_remove_from_task'),
    path('task/<int:task_pk>/teams/add/', views.team_add_to_task, name='team_add_to_task'),
    path('task/<int:task_pk>/teams/remove/', views.team_remove_from_task, name='team_remove_from_task'),
    
    path('task/<int:task_pk>/comment/add/', views.task_comment_add, name='task_comment_add'),

    path('task/<int:task_pk>/search-members/', views.task_member_search, name='task_member_search'),
    path('task/<int:task_pk>/search-directions/', views.task_direction_search, name='task_direction_search'),
    path('task/<int:task_pk>/search-teams/', views.task_team_search, name='task_team_search'),
]