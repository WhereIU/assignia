from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('about/', views.about, name='about'),
    path('tutorials/', views.tutorials, name='tutorials'),
]