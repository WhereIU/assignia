from django.urls import path

from . import views


app_name = 'project_teams'

urlpatterns = [
    path('tab/<int:direction_pk>/', views.teams_tab, name='teams_tab'),

    path('new/<int:direction_pk>/create/', views.team_create, name='team_create'),
    path('team/<int:team_pk>/update/', views.team_update, name='team_update'),
    path('team/<int:team_pk>/delete/', views.team_delete, name='team_delete'),
    path('team/<int:team_pk>/hard-delete/', views.team_hard_delete, name='team_hard_delete'),
    path('form/<int:team_pk>/delete/', views.team_delete_confirm, name='team_delete_confirm'),
    path('team/<int:team_pk>/restore/', views.team_restore, name='team_restore'),
    
    path('team/<int:team_pk>/members/', views.team_members, name='team_members'),
    path('team/<int:team_pk>/members/search/', views.team_member_search, name='team_member_search'),
    path('team/<int:team_pk>/members/add/<int:user_pk>/', views.team_member_add, name='team_member_add'),
    path('team/<int:team_pk>/members/remove/<int:user_pk>/', views.team_member_remove, name='team_member_remove'),
    path('team/<int:team_pk>/members/remove/<int:user_pk>/confirm/', views.team_member_delete_confirm, name='team_member_delete_confirm'),
    
    path('form/<int:direction_pk>/create/', views.team_create_form, name='team_create_form'),
    path('form/<int:direction_pk>/<int:team_pk>/edit/', views.team_edit_form, name='team_edit_form'),
]