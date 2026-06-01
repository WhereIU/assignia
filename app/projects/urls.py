from django.urls import path

from . import views


app_name = 'projects'

urlpatterns = [
    path('', views.available_projects, name='available_projects'),

    path('new/project/create/', views.project_create, name='project_create'),
    path('project/<str:username>/<str:slug>/', views.project_detail, name='project_detail'),
    path('project/<str:username>/<str:slug>/join/', views.project_join, name='project_join'),
    path('project/<str:username>/<str:slug>/update/', views.project_update, name='project_update'),

    path('form/project/<str:username>/<str:slug>/settings/', views.project_settings_form, name='project_settings_form'),

    path('project/<str:username>/<str:slug>/members/', views.members_tab, name='members_tab'),
    path('project/<str:username>/<str:slug>/settings/', views.project_settings_tab, name='project_settings_tab'),

    path('project/<str:username>/<str:slug>/invite/', views.invitation_send, name='invitation_send'),
    path('project/<str:username>/<str:slug>/invite/<int:invitation_pk>/cancel/', views.invitation_cancel, name='invitation_cancel'),
    path('invitation/<int:invitation_pk>/accept/', views.invitation_accept, name='invitation_accept'),
    path('invitation/<int:invitation_pk>/decline/', views.invitation_decline, name='invitation_decline'),
    
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/remove/', views.member_remove, name='member_remove'),
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/update/role/', views.member_update_role, name='member_update_role'),
]