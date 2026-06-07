from __future__ import annotations
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from project_members.views import _render_members_tab
from common.selectors import get_page_filters, get_paginated_page
from common.services import message_success, message_error, message_info
from project_members.permissions import (
    can_access_project,
    is_admin_or_owner,
    is_privileged,
    is_project_member,
    is_project_owner,
)
from project_members.constants import ProjectRole
from project_tasks.selectors import get_tasks_by_project
from project_members.selectors import get_member_role
from project_members.services import create_membership as create_project_membership
from project_tasks.services import apply_tasks_filters
from users.selectors import get_user_by_username

from .constants import InvitationStatus
from .forms import ProjectCreateForm
from .selectors import (
    get_available_projects,
    get_invitation_by_pk,
    get_pending_invitations,
    get_project
)
from .services import (
    accept_invitation,
    cancel_invitation,
    create_project,
    decline_invitation,
    send_project_invitation,
    update_project,
)

if TYPE_CHECKING:
    from projects.models import Project


def available_projects(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    projects_queryset = get_available_projects(request.user, query=query)
    
    page_number = request.GET.get("page", 1)
    page_obj = get_paginated_page(projects_queryset, page=page_number, per_page=6)
    
    context = {
        "projects": page_obj, 
        "query": query
    }
    
    if request.headers.get("HX-Request"):
        return render(
            request, 
            "projects/partials/_projects_grid.html", 
            context
        )
        
    return render(
        request, 
        "projects/available_projects.html", 
        context
    )


@login_required
def project_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProjectCreateForm(request.POST, initial={"owner": request.user})
        if form.is_valid():
            project = create_project(form=form, user=request.user)
            create_project_membership(
                user=request.user, project=project, role="owner"
            )
            message_success(request, f"Проект «{project.name}» создан!")
            return redirect(
                "projects:project_detail",
                username=request.user.username,
                slug=project.slug,
            )
    else:
        form = ProjectCreateForm(initial={"owner": request.user})
    return render(request, "projects/project_create.html", {"form": form})


def project_detail(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not can_access_project(request.user, project):
        if not request.user.is_authenticated:
            return redirect("users:login")
        return HttpResponseForbidden("Вы не участник проекта")

    tasks = get_tasks_by_project(project)
    is_member = is_project_member(request.user, project)
    is_priv = is_privileged(request.user, project)

    filters = get_page_filters(request)

    if request.headers.get("HX-Request"):
        if any(request.GET.get(p) for p in ("status", "priority", "risk", "q")):
            tasks = apply_tasks_filters(tasks, filters)
            return render(
                request,
                "tasks/partials/_task_list.html",
                {"tasks": tasks, "show_take_button": True, "filters": filters},
            )
        return render(
            request,
            "tasks/partials/_tasks_tab.html",
            {
                "tasks": tasks,
                "project": project,
                "is_member": is_member,
                "filters": filters,
            },
        )

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "tasks": tasks,
            "is_member": is_member,
            "is_privileged": is_priv,
            "filters": filters,
        },
    )


@login_required
def project_join(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not project.is_public:
        return HttpResponseForbidden("Нельзя вступить в приватный проект.")
        
    if is_project_member(request.user, project):
        message_info(request, "Вы уже участник этого проекта.")
    else:
        create_project_membership(
            user=request.user, project=project, role="participant"
        )
        message_success(request, f"Вы вступили в проект «{project.name}»!")
        
    return redirect(
        "projects:project_detail", username=username, slug=slug
    )


def project_delete(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_project_owner(user=request.user, project=project):
        return HttpResponseForbidden("Нельзя удалить чужой проект")
        
    project.delete()
    message_success(request, f"Проект «{project.name}» успешно удалён.")

    response = HttpResponse(status=200)
    response["HX-Redirect"] = reverse("projects:available_projects")
    return response


@login_required
@require_http_methods(["GET"])
def project_delete_confirm(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_project_owner(user=request.user, project=project):
        return HttpResponseForbidden("У вас нет прав для удаления этого проекта")
        
    return render(request, "projects/partials/_project_delete_confirm.html", {
        "project": project
    })


@login_required
def invitation_form(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    return _render_invitation_form(request, project, username, slug)


@login_required
@require_http_methods(["POST"])
def invitation_send(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    recipient_username = request.POST.get("username", "").strip()
    role = request.POST.get("role", "participant")

    if not recipient_username:
        message_error(request, "Укажите имя пользователя")
        return _render_invitation_form(request, project, username, slug, typed_username=recipient_username, selected_role=role)

    recipient = get_user_by_username(recipient_username)
    if recipient is None:
        message_error(request, "Пользователь не найден")
        return _render_invitation_form(request, project, username, slug, typed_username=recipient_username, selected_role=role)

    try:
        send_project_invitation(
            sender=request.user,
            recipient=recipient,
            project=project,
            role=role,
        )
    except ValidationError as e:
        message_error(request, e.message)
        return _render_invitation_form(request, project, username, slug, typed_username=recipient_username, selected_role=role)

    message_success(request, f"Приглашение отправлено {recipient.username}")
    
    response = _render_members_tab(request, project)
    response["HX-Retarget"] = "#tab-content"
    response["HX-Reswap"] = "innerHTML"
    return response


def _render_invitation_form(
    request: HttpRequest, 
    project: Project, 
    username: str, 
    slug: str, 
    typed_username: str = "", 
    selected_role: str = "participant"
) -> HttpResponse:
    return render(
        request,
        "projects/partials/_invitation_form.html",
        {
            "project": project,
            "membership_roles": ProjectRole.choices,
            "selected_role": selected_role,
            "typed_username": typed_username,
            "submit_url": reverse(
                "projects:invitation_send",
                kwargs={"username": username, "slug": slug},
            ),
        },
    )


@login_required
def invitation_cancel(
    request: HttpRequest, username: str, slug: str, invitation_pk: int
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    invitation = get_invitation_by_pk(
        pk=invitation_pk, project=project, status=InvitationStatus.PENDING
    )
    if not invitation:
        raise Http404("Приглашение не найдено")

    cancel_invitation(invitation=invitation)
    message_success(
        request, f"Приглашение {invitation.recipient.username} отменено"
    )

    pending = get_pending_invitations(project=project)
    return render(
        request,
        "projects/partials/_invitations_pending.html",
        {
            "pending_invitations": pending,
            "project": project,
            "actor_role": get_member_role(request.user, project),
        },
    )


@login_required
@require_http_methods(["POST"])
def invitation_accept(request: HttpRequest, invitation_pk: int) -> HttpResponse:
    invitation = get_invitation_by_pk(
        pk=invitation_pk, recipient=request.user, status=InvitationStatus.PENDING
    )
    if not invitation:
        raise Http404("Приглашение не найдено")
        
    project = invitation.project
    
    if is_project_member(request.user, project):
        message_info(request, "Вы уже участник проекта")
    else:
        accept_invitation(invitation=invitation, user=request.user)
        message_success(request, f"Вы вступили в проект «{project.name}»")

    if request.GET.get("variant") == "inline":
        return render(
            request,
            "projects/partials/_invitation_inline_result.html",
            {"invitation": invitation, "status": "accepted"},
        )

    response = HttpResponse(status=200)
    response["HX-Redirect"] = reverse("projects:project_detail", kwargs={"username": project.owner.username, "slug": project.slug})
    return response


@login_required
@require_http_methods(["POST"])
def invitation_decline(request: HttpRequest, invitation_pk: int) -> HttpResponse:
    invitation = get_invitation_by_pk(
        pk=invitation_pk, recipient=request.user, status=InvitationStatus.PENDING
    )
    if not invitation:
        raise Http404("Приглашение не найдено")
        
    decline_invitation(invitation=invitation)
    message_info(request, "Приглашение отклонено")

    if request.GET.get("variant") == "inline":
        return render(
            request,
            "projects/partials/_invitation_inline_result.html",
            {"invitation": invitation, "status": "declined"},
        )

    response = HttpResponse(status=200)
    response["HX-Redirect"] = reverse("core:home")
    return response


@login_required
def project_settings_tab(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    return render(
        request,
        "projects/partials/_project_settings.html",
        {"project": project},
    )


@login_required
def project_settings_form(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    return render(
        request,
        "projects/partials/_project_settings_form.html",
        {
            "project": project,
            "submit_url": reverse(
                "projects:project_update",
                kwargs={"username": username, "slug": slug},
            ),
        },
    )


@login_required
@require_http_methods(["POST"])
def project_update(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    is_public = request.POST.get("is_public") == "on"

    if not name:
        message_error(request, "Название проекта не может быть пустым")
        return redirect(
            "projects:project_settings_tab",
            username=username,
            slug=slug,
        )

    if not get_member_role(request.user, project) == ProjectRole.OWNER:
        is_public = project.is_public

    update_project(
        project=project,
        name=name,
        description=description,
        is_public=is_public,
    )
    message_success(request, "Настройки проекта обновлены")
    return redirect(
        "projects:project_settings_tab",
        username=username,
        slug=slug,
    )