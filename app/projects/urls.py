from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.available_projects, name='available_projects'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new/', views.create_project, name='create_project'),

    path('project/<str:username>/<str:slug>/tab/analytics/', views.project_analytics_tab, name='project_analytics_tab'),

    path('project/<str:username>/<str:slug>/', views.detail_project, name='detail_project'),
    path('project/<str:username>/<str:slug>/tasks/', views.project_tasks, name='project_tasks'),
    path('project/<str:username>/<str:slug>/join/', views.join_project, name='join_project'),

    path('project/<str:username>/<str:slug>/members/', views.project_members, name='project_members'),
    path('project/<str:username>/<str:slug>/invite/', views.send_invitation, name='send_invitation'),
    path('invitation/<int:invitation_pk>/invite/accept/', views.accept_invitation, name='accept_invitation'),
    path('invitation/<int:invitation_pk>/invite/decline/', views.decline_invitation, name='decline_invitation'),
    path('project/<str:username>/<str:slug>/invite/<int:invitation_pk>/cancel/', views.cancel_invitation, name='cancel_invitation'),
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/remove/', views.remove_member, name='remove_member'),
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/update/role/', views.change_member_role, name='change_member_role'),
]
