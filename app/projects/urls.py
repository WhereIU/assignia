from django.urls import path

from . import views


app_name = 'projects'

urlpatterns = [
    path('', views.available_projects, name='available_projects'),

    path('new/project/create/', views.project_create, name='project_create'),
    path('project/<str:username>/<str:slug>/', views.project_detail, name='project_detail'),
    path("project/<str:username>/<slug:slug>/overview/", views.project_overview_tab, name="project_overview_tab"),
    path('project/<str:username>/<str:slug>/update/', views.project_update, name='project_update'),
    path('project/<str:username>/<slug:slug>/delete/', views.project_delete, name='project_delete'),
    path('project/<str:username>/<slug:slug>/delete/confirm/', views.project_delete_confirm, name='project_delete_confirm'),

    path('form/project/<str:username>/<str:slug>/settings/', views.project_settings_form, name='project_settings_form'),
    
    path('project/<str:username>/<str:slug>/settings/', views.project_settings_tab, name='project_settings_tab'),

    path('project/<str:username>/<str:slug>/invite/', views.invitation_send, name='invitation_send'),
    path('project/<str:username>/<str:slug>/invite/<int:invitation_pk>/cancel/', views.invitation_cancel, name='invitation_cancel'),
    path('invitation/<int:invitation_pk>/accept/', views.invitation_accept, name='invitation_accept'),
    path('invitation/<int:invitation_pk>/decline/', views.invitation_decline, name='invitation_decline'),
    
    path('invitation/<str:username>/<str:slug>/', views.invitation_form, name="invitation_form"),

]