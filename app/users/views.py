from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import (
    LoginForm,
    ProfileEditForm,
    UserCreationForm,
    AccountEmailForm,
    PasswordChangeForm,
)
from .models import User
from .services import send_email_confirmation, confirm_email_token

from projects.models import Project


class AssigniaLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def get_initial(self):
        initial = super().get_initial()

        data = self.request.session.pop("login_prefill", None)
        if data:
            initial.update(data)

        return initial

    def form_invalid(self, form):
        if self.request.method == "POST":
            messages.error(
                self.request,
                "Неверный логин или пароль."
            )
        return super().form_invalid(form)

class AssigniaLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            send_email_confirmation(user)
            messages.success(
                request,
                "Подтвердите email для активации аккаунта."
            )
            request.session["login_prefill"] = {
                "username": user.username,
                "password": form.cleaned_data.get("password1"),
            }

            return redirect("users:login")
    else:
        form = UserCreationForm()
    return render(request, "users/register.html", {"form": form})


def confirm_email(request, token):
    user = confirm_email_token(token)
    if not user:
        messages.error(request, "Ссылка недействительна или устарела.")
        return redirect("users:register")

    login(request, user)
    messages.success(request, "Email подтверждён. Добро пожаловать.")
    return redirect("core:home")


def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    owned_projects = Project.objects.filter(
        owner=profile_user,
        is_public=True
    ).order_by("-created_at")

    contributed_projects = Project.objects.filter(
        projectmembership__user=profile_user,
        is_public=True
    ).exclude(owner=profile_user).distinct().order_by("-created_at")

    return render(request, "users/public_profile.html", {
        "profile_user": profile_user,
        "owned_projects": owned_projects,
        "contributed_projects": contributed_projects,
    })


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("users:profile")
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "users/profile.html", {"form": form})


@login_required
def account(request):
    email_form = AccountEmailForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    if request.method == "POST":
        if "change_email" in request.POST:
            if request.user.pending_email:
                messages.error(request, "У вас уже есть неподтверждённый email.")
                return render(request, "users/partials/_account_email_display.html", {"user": request.user})

            email_form = AccountEmailForm(request.POST, instance=request.user)
            if email_form.is_valid():
                new_email = email_form.cleaned_data["email"]
                try:
                    send_email_confirmation(request.user, new_email)
                    request.user.refresh_from_db()
                    messages.success(request, "Письмо подтверждения отправлено.")
                except Exception:
                    messages.error(request, "Не удалось отправить письмо.")
                return render(request, "users/partials/_account_email_display.html", {"user": request.user})

            return render(request, "users/partials/_account_email_form.html", {"email_form": email_form})

        elif "change_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)

                messages.success(request, "Пароль изменён.")
                return render(request, "users/partials/_account_password_display.html", {"user": request.user})
            
            return render(request,"users/partials/_account_password_form.html", {"password_form": password_form})
        
    return render(request, "users/account.html", {"email_form": email_form, "password_form": password_form})


@login_required
@require_POST
def cancel_pending_email(request):
    request.user.pending_email = None
    request.user.save(update_fields=["pending_email"])

    messages.success(request, "Подтверждение email отменено.")
    return render(request, "users/partials/_account_email_display.html", {"user": request.user})


@login_required
def account_email_form(request):
    form = AccountEmailForm(instance=request.user)
    return render(request, "users/partials/_account_email_form.html", {
        "email_form": form
    })


@login_required
def account_email_display(request):
    return render(request, "users/partials/_account_email_display.html", {
        "user": request.user
    })


@login_required
def account_password_form(request):
    form = PasswordChangeForm(request.user)
    return render(request, "users/partials/_account_password_form.html", {
        "password_form": form
    })


@login_required
def account_password_display(request):
    return render(request, "users/partials/_account_password_display.html", {
        "user": request.user
    })
