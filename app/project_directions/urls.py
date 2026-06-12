from django.urls import path

from . import views


app_name = 'project_directions'

urlpatterns = [
    path('tab/<str:username>/<str:slug>/', views.directions_tab, name='directions_tab'),

    path('new/<str:username>/<str:slug>/create/', views.direction_create, name='direction_create'),
    path('direction/<int:direction_pk>/update/', views.direction_update, name='direction_update'),
    path('direction/<int:direction_pk>/delete/', views.direction_delete, name='direction_delete'),
    path('direction/<int:direction_pk>/hard-delete/', views.direction_hard_delete, name='direction_hard_delete'),
    path('form/<int:direction_pk>/delete-confirm/', views.direction_delete_confirm, name='direction_delete_confirm'),
    path('direction/<int:direction_pk>/restore/', views.direction_restore, name='direction_restore'),
    
    path('form/<str:username>/<str:slug>/create/', views.direction_create_form, name='direction_create_form'),
    path('form/<int:direction_pk>/edit/', views.direction_edit_form, name='direction_edit_form'),
]