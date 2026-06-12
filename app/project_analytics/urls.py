from django.urls import path

from . import views


app_name = 'project_analytics'

urlpatterns = [
    path('project/<str:username>/<slug:slug>/analytics/', views.analytics_tab, name='analytics_tab'),
    path('project/<str:username>/<slug:slug>/analytics/widget/', views.analytics_widget_element, name='analytics_widget'),
]