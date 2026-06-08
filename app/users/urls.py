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
    path('profile/delete/avatar/', views.delete_avatar, name='delete_avatar'),
    path('settings/account/form/email/', views.account_email_form, name='account_email_form'),
    path('settings/account/form/password/', views.account_password_form, name='account_password_form'),
    path('settings/account/email/display/', views.account_email_display, name='account_email_display'),
    path('settings/account/email/cancel/', views.cancel_pending_email, name='cancel_pending_email'),
    path('settings/account/password/display/', views.account_password_display, name='account_password_display'),

    path('settings/account/email/confirm/<str:token>/', views.confirm_email, name='confirm_email'),
]