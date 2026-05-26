from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('tab/<str:username>/<str:slug>/', views.tasks_tab, name='tasks_tab'),

    path('new/<str:username>/<str:slug>/create/', views.task_create, name='task_create'),
    path('task/<int:task_pk>/', views.task_detail, name='task_detail'),
    path('task/<int:task_pk>/take/', views.task_take, name='task_take'),
    path('task/<int:task_pk>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_pk>/save/', views.task_save, name='task_save'),
    path('task/<int:task_pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:task_pk>/restore/', views.task_restore, name='task_restore'),
    path('task/<int:task_pk>/status/update/', views.task_update_status, name='task_update_status'),
    path('task/<int:task_pk>/priority/update/', views.task_update_priority, name='task_update_priority'),
    path('task/<int:task_pk>/risk/update/', views.task_update_risk, name='task_update_risk'),
    path('task/<int:task_pk>/assignees/add/', views.assignee_add, name='assignee_add'),
    path('task/<int:task_pk>/assignees/remove/', views.assignee_remove, name='assignee_remove'),
    path('task/<int:task_pk>/directions/add/', views.direction_add_to_task, name='direction_add_to_task'),
    path('task/<int:task_pk>/directions/remove/', views.direction_remove_from_task, name='direction_remove_from_task'),
    path('task/<int:task_pk>/teams/add/', views.team_add_to_task, name='team_add_to_task'),
    path('task/<int:task_pk>/teams/remove/', views.team_remove_from_task, name='team_remove_from_task'),
    
    path('task/<int:task_pk>/comment/add/', views.comment_add, name='comment_add'),

    path('task/<int:task_pk>/search-members/', views.member_search, name='member_search'),
    path('task/<int:task_pk>/search-directions/', views.direction_search, name='direction_search'),
    path('task/<int:task_pk>/search-teams/', views.team_search, name='team_search'),
]