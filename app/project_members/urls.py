from django.urls import path

from . import views


app_name = 'project_members'

urlpatterns = [
    path('project/<str:username>/<str:slug>/members/', views.members_tab, name='members_tab'),

    path('project/<str:username>/<str:slug>/members/<int:user_pk>/remove/', views.member_remove, name='member_remove'),
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/remove/confirm/', views.member_remove_confirm, name='member_remove_confirm'),
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/update/role/', views.member_update_role, name='member_update_role'),
    path('project/<str:username>/<str:slug>/members/<int:user_pk>/update/role/form/', views.member_update_role_form, name='member_update_role_form'),
]