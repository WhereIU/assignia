from django.urls import path

from . import views


app_name = 'project_analytics'

urlpatterns = [
    path('project/<str:username>/<str:slug>/analytics/', views.analytics_tab, name='analytics_tab')
]