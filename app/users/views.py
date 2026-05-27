from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.urls import reverse
from django.core.cache import cache

from projects.models import Project

from .forms import ProfileEditForm, UserCreationForm, AccountEmailForm, PasswordChangeForm
from .models import User
from .utils import send_email_confirmation

class AssigniaLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True


class AssigniaLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('projects:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    owned_projects = Project.objects.filter(owner=profile_user, is_public=True).order_by('-created_at')
    contributed_projects = Project.objects.filter(
        projectmembership__user=profile_user,
        is_public=True
    ).exclude(owner=profile_user).distinct().order_by('-created_at')

    return render(request, 'users/public_profile.html', {
        'profile_user': profile_user,
        'owned_projects': owned_projects,
        'contributed_projects': contributed_projects,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})


@login_required
def account(request):
    email_form = AccountEmailForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'change_email' in request.POST:
            email_form = AccountEmailForm(request.POST, instance=request.user)
            if email_form.is_valid():
                new_email = email_form.cleaned_data['email']
                send_email_confirmation(request.user, new_email)
                messages.success(request, 'Письмо с подтверждением отправлено на новый email.')
                return render(request, 'users/partials/_account_email_display.html', {'user': request.user})
            else:
                return render(request, 'users/partials/_account_email_form.html', {'email_form': email_form})

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль изменён.')
                return render(request, 'users/partials/_account_password_display.html', {'user': request.user})
            else:
                return render(request, 'users/partials/_account_password_form.html', {'password_form': password_form})

    return render(request, 'users/account.html', {
        'email_form': email_form,
        'password_form': password_form,
    })


def confirm_email(request, token):
    cache_key = f'email_confirmation:{token}'
    data = cache.get(cache_key)
    if not data:
        messages.error(request, 'Ссылка недействительна или истекла.')
        return redirect('core:home')
    
    user = User.objects.get(pk=data['user_id'])
    user.email = data['new_email']
    user.save()
    cache.delete(cache_key)
    messages.success(request, 'Email успешно подтверждён.')
    return redirect('users:account')


@login_required
def account_email_form(request):
    form = AccountEmailForm(instance=request.user)
    return render(request, 'users/partials/_account_email_form.html', {'email_form': form})


@login_required
def account_password_form(request):
    form = PasswordChangeForm(request.user)
    return render(request, 'users/partials/_account_password_form.html', {'password_form': form})

@login_required
def account_email_display(request):
    return render(request, 'users/partials/_account_email_display.html', {'user': request.user})


@login_required
def account_password_display(request):
    return render(request, 'users/partials/_account_password_display.html', {'user': request.user})


def notifications_settings(request):
    return render(request, 'users/settings_stub.html', {'title': 'Уведомления'})


def email_settings(request):
    return render(request, 'users/settings_stub.html', {'title': 'Почта'})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль изменён.')
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})
