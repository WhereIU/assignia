from django.urls import path

from . import views

app_name = 'teams'

urlpatterns = [
    path('tab/<int:direction_pk>/', views.team_tab, name='teams_tab'),

    path('new/<int:direction_pk>/create/', views.team_create, name='team_create'),
    path('team/<int:team_pk>/update/', views.team_update, name='team_update'),
    path('team/<int:team_pk>/delete/', views.team_delete, name='team_delete'),
    path('team/<int:team_pk>/restore/', views.team_restore, name='team_restore'),

    path('form/<int:direction_pk>/create/', views.team_create_form, name='team_create_form'),
    path('form/<int:direction_pk>/<int:team_pk>/edit/', views.team_edit_form, name='team_edit_form'),
]