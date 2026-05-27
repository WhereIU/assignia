from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.AssigniaLoginView.as_view(), name='login'),
    path('logout/', views.AssigniaLogoutView.as_view(), name='logout'),

    path('profile/<str:username>/', views.public_profile, name='public_profile'),

    path('settings/profile/', views.profile, name='profile'),
    path('settings/account/', views.account, name='account'),
    path('settings/account/form/email/', views.account_email_form, name='account_email_form'),
    path('settings/account/form/password/', views.account_password_form, name='account_password_form'),
    path('settings/account/email-display/', views.account_email_display, name='account_email_display'),
    path('settings/account/password-display/', views.account_password_display, name='account_password_display'),
    path('settings/notifications/', views.notifications_settings, name='notifications_settings'),
    path('settings/email/', views.email_settings, name='email_settings'),
]