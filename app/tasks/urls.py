from django.urls import path

from . import views

app_name = 'tasks'


urlpatterns = [
    path('task/<str:username>/<str:slug>/new/', views.create_task, name='create_task'),
    path('task/<int:task_pk>/', views.detail_task, name='detail_task'),
    path('task/<int:task_pk>/take/', views.take_task, name='take_task'),
    path('task/<int:task_pk>/edit/', views.edit_task, name='edit_task'),
    path('task/<int:task_pk>/save/', views.save_task, name='save_task'),
    path('task/<int:task_pk>/delete/', views.delete_task, name='delete_task'),
    path('task/<int:task_pk>/restore/', views.restore_task, name='restore_task'),
    path('task/<int:task_pk>/status/update/', views.change_status, name='change_status'),
    path('task/<int:task_pk>/priority/update/', views.change_priority, name='change_priority'),
    path('task/<int:task_pk>/risk/update', views.change_risk, name='change_risk'),
    path('task/<int:task_pk>/comment/add/', views.add_comment, name='add_comment'),
    path('task/<int:task_pk>/assignees/add/', views.add_assignee, name='add_assignee'),
    path('task/<int:task_pk>/assignees/remove/', views.remove_assignee, name='remove_assignee'),

    path('task/<int:task_pk>/search-members/', views.search_members, name='search_members'),
    path('task/<int:task_pk>/search-directions/', views.search_directions, name='search_directions'),   
    path('task/<int:task_pk>/directions/add/', views.add_direction, name='add_direction'),
    path('task/<int:task_pk>/directions/remove/', views.remove_direction, name='remove_direction'),

    path('request/<str:username>/<str:slug>/new/', views.create_request, name='create_request'),
    path('request/<str:username>/<str:slug>/tab/requests/', views.project_requests_tab, name='project_requests_tab'),
    path('request/<str:username>/<str:slug>/form/create/', views.request_create_form, name='request_create_form'),
    path('request/<str:username>/<str:slug>/submit/create/', views.request_create_submit, name='request_create_submit'),
    path('request/<str:username>/<str:slug>/<int:request_pk>/', views.detail_request, name='detail_request'),
    path('request/<str:username>/<str:slug>/<int:request_pk>/message/add/', views.request_add_message, name='request_add_message'),
    path('request/<str:username>/<str:slug>/<int:request_pk>/convert/', views.request_convert_to_task, name='request_convert_to_task'),
    path('request/<str:username>/<str:slug>/<int:request_pk>/delete/', views.delete_request, name='delete_request'),
]
