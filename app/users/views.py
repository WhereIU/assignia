from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from common.services import message_error, message_success
from projects.selectors import get_all_public_projects_of_user

from .forms import (
    AccountEmailForm,
    LoginForm,
    PasswordChangeForm,
    ProfileEditForm,
    UserCreationForm,
)
from .selectors import get_profile_projects_context, get_user_by_username
from .services import (
    cancel_pending_email as cancel_new_email,
    change_user_email,
    delete_user_avatar,
    send_registration_confirmation,
    create_user_from_cache,
)


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
            message_error(self.request, "Неверный логин или пароль.")
        return super().form_invalid(form)


class AssigniaLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


def register(request: HttpRequest) -> HttpResponse:
    """Handle new user registration."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                send_registration_confirmation(form.cleaned_data)
            except RuntimeError as exc:
                message_error(request, str(exc))
                return render(request, "users/register.html", {"form": form})

            message_success(request, "Подтвердите email для активации аккаунта.")
            
            request.session["login_prefill"] = {
                "username": form.cleaned_data.get("username"),
                "password": form.cleaned_data.get("password1"),
            }
            return redirect("users:login")
    else:
        form = UserCreationForm()
    return render(request, "users/register.html", {"form": form})


def confirm_email(request: HttpRequest, token: str) -> HttpResponse:
    """Confirm token from cache, create active user in DB and log them in."""
    user = create_user_from_cache(token)
    
    if not user:
        message_error(request, "Ссылка недействительна, устарела или данные уже заняты.")
        return redirect("users:register")
        
    login(request, user)
    message_success(request, "Email подтверждён. Добро пожаловать.")
    return redirect("core:home")


def public_profile(request: HttpRequest, username: str) -> HttpResponse:
    """Render public profile with user's projects and search filter."""
    profile_user = get_user_by_username(username)
    if not profile_user:
        raise Http404("Пользователь не найден")

    projects_queryset = get_all_public_projects_of_user(profile_user)
    
    projects_context = get_profile_projects_context(
        projects_queryset=projects_queryset,
        search_query=request.GET.get("q", ""),
        page_number=request.GET.get("page", "1")
    )

    context = {
        "profile_user": profile_user,
        "total_projects_count": projects_queryset.count(),
        **projects_context
    }

    if request.headers.get("HX-Request"):
        return render(request, "projects/partials/_profile_projects.html", context)

    return render(request, "users/public_profile.html", context)


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """Edit profile data."""
    if request.method == "POST":
        if "delete_avatar" in request.POST:
            delete_user_avatar(request.user)
            message_success(request, "Аватар успешно удалён.")
            return redirect("users:profile")

        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            message_success(request, "Профиль обновлён.")
            return redirect("users:profile")
    else:
        form = ProfileEditForm(instance=request.user)
        
    return render(request, "users/profile.html", {"form": form})


@login_required
def delete_avatar(request: HttpRequest) -> HttpResponse:
    """Handle avatar deletion modal and action via HTMX."""
    if request.method == "POST":
        delete_user_avatar(request.user)
        message_success(request, "Аватар успешно удалён.")
        
        response = render(request, "users/partials/_user_block.html", {"user": request.user})
        return response

    return render(request, "users/partials/_delete_avatar_confirm.html")


@login_required
def account(request: HttpRequest) -> HttpResponse:
    """Manage account settings."""
    email_form = AccountEmailForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        if "change_email" in request.POST:
            return _handle_change_email(request)
        elif "change_password" in request.POST:
            return _handle_change_password(request)

    return render(
        request,
        "users/account.html",
        {"email_form": email_form, "password_form": password_form},
    )


def _handle_change_email(request: HttpRequest) -> HttpResponse:
    """Process email change request."""
    email_form = AccountEmailForm(request.POST, instance=request.user)
    if email_form.is_valid():
        new_email = email_form.cleaned_data["email"]
        try:
            change_user_email(request.user, new_email)
            message_success(request, "Письмо подтверждения отправлено.")
        except (ValueError, RuntimeError) as e:
            message_error(request, str(e))
        return render(
            request,
            "users/partials/_account_email_display.html",
            {"user": request.user},
        )
    return render(
        request,
        "users/partials/_account_email_form.html",
        {"email_form": email_form},
    )


def _handle_change_password(request: HttpRequest) -> HttpResponse:
    """Process password change request."""
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        message_success(request, "Пароль изменён.")
        return render(
            request,
            "users/partials/_account_password_display.html",
            {"user": request.user},
        )
    return render(
        request,
        "users/partials/_account_password_form.html",
        {"password_form": form},
    )


@login_required
@require_POST
def cancel_pending_email(request: HttpRequest) -> HttpResponse:
    """Cancel pending email confirmation."""
    cancel_new_email(request.user)
    message_success(request, "Подтверждение email отменено.")
    return render(
        request,
        "users/partials/_account_email_display.html",
        {"user": request.user},
    )


@login_required
def account_email_form(request: HttpRequest) -> HttpResponse:
    """Render the email editing partial form."""
    form = AccountEmailForm(instance=request.user)
    return render(
        request, "users/partials/_account_email_form.html", {"email_form": form}
    )


@login_required
def account_email_display(request: HttpRequest) -> HttpResponse:
    """Render the email display partial view."""
    return render(
        request,
        "users/partials/_account_email_display.html",
        {"user": request.user},
    )


@login_required
def account_password_form(request: HttpRequest) -> HttpResponse:
    """Render the password change partial form."""
    form = PasswordChangeForm(request.user)
    return render(
        request,
        "users/partials/_account_password_form.html",
        {"password_form": form},
    )


@login_required
def account_password_display(request: HttpRequest) -> HttpResponse:
    """Render the password display partial view."""
    return render(
        request,
        "users/partials/_account_password_display.html",
        {"user": request.user},
    )
