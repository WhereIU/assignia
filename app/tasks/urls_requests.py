from django.urls import path

from . import views

app_name = 'requests'

urlpatterns = [
    path('tab/<str:username>/<str:slug>/', views.request_tab, name='requests_tab'),
    
    path('new/<str:username>/<str:slug>/create/', views.request_create, name='request_create'),
    path('request/<int:request_pk>/', views.request_detail, name='request_detail'),
    path('request/<int:request_pk>/convert/', views.request_convert, name='request_convert'),
    path('request/<int:request_pk>/delete/', views.request_delete, name='request_delete'),

    path('request/<int:request_pk>/message/add/', views.request_message_add, name='request_message_add'),

    path('form/<str:username>/<str:slug>/create/', views.request_create_form, name='request_create_form'),
    path('submit/<str:username>/<str:slug>/create/', views.request_create_submit, name='request_create_submit'),
]