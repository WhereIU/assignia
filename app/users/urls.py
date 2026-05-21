from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.AssigniaLoginView.as_view(), name='login'),
    path('logout/', views.AssigniaLogoutView.as_view(), name='logout'),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    path('settings/profile/', views.profile, name='profile'),
    path('settings/password/', views.change_password, name='change_password'),
]