from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from projects.models import Project

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User


class AssigniaLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True


class AssigniaLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('projects:dashboard')
    else:
        form = CustomUserCreationForm()
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
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('users:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})


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
