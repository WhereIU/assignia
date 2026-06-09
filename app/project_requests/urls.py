from django.urls import path

from . import views


app_name = 'requests'

urlpatterns = [
    path('tab/<str:username>/<str:slug>/', views.requests_tab, name='requests_tab'),
    
    path('new/<str:username>/<str:slug>/create/', views.request_create, name='request_create'),
    path('request/<int:request_pk>/', views.request_detail, name='request_detail'),
    path('request/<int:request_pk>/convert/', views.request_convert, name='request_convert'),
    path('request/<int:request_pk>/delete/', views.request_delete, name='request_delete'),
    path('request/<int:request_pk>/decline/', views.request_decline, name='request_decline'),

    path('request/<int:request_pk>/message/add/', views.request_message_add, name='request_message_add'),

    path('form/<str:username>/<str:slug>/create/', views.request_create, name='request_create_form'),
]