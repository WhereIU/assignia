from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    # path('tutorials/', views.tutorials, name='tutorials'),
    # path('about/', views.about, name='about'),
]