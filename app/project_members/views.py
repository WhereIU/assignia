from __future__ import annotations
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import remove_member, update_member_role
from .permissions import (
    ProjectRole,
    can_manage_member,
    get_membership,
    is_admin_or_owner,
)

from projects.selectors import get_project, get_pending_invitations
from project_members.selectors import get_member_role, get_project_memberships, search_project_memberships
from common.services import message_success, message_error

if TYPE_CHECKING:
    from projects.models import Project


def _render_members_tab(
    request: HttpRequest,
    project: Project,
    *,
    search_query: str = "",
    page: int = 1,
) -> HttpResponse:
    """Render members tab."""
    members = (
        get_project_memberships(project=project)
        if search_query
        else search_project_memberships(project=project, query=search_query)
    )
    paginator = Paginator(members, 10)
    page_obj = paginator.get_page(page)

    actor_role = get_member_role(request.user, project)
    pending = get_pending_invitations(project=project)

    template = (
        "members/partials/_members_list.html"
        if request.headers.get("HX-Target") == "members-container"
        else "members/partials/_members_tab.html"
    )

    return render(
        request,
        template,
        {
            "project": project,
            "members": page_obj,
            "actor_role": actor_role,
            "pending_invitations": pending,
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
def members_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    search = request.GET.get("search", "")
    page = request.GET.get("page", 1)
    return _render_members_tab(request, project, search_query=search, page=page)


@login_required
@require_http_methods(["POST"])
def member_update_role(
    request: HttpRequest, username: str, slug: str, user_pk: int
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    target = get_membership(project=project, user_pk=user_pk)

    if not can_manage_member(request.user, target, project):
        return HttpResponseForbidden("Недостаточно прав")

    new_role = request.POST.get("role")
    if new_role not in ProjectRole.values:
        message_error(request, "Неверная роль")
        return _render_members_tab(request, project)

    actor_membership = get_membership(request.user, project)
    try:
        update_member_role(
            actor_membership=actor_membership,
            target_membership=target,
            new_role=new_role,
        )
    except ValidationError as e:
        message_error(request, str(e))
        return _render_members_tab(request, project)

    message_success(
        request, f"Роль {target.user.username} изменена на {new_role}"
    )
    return _render_members_tab(request, project)


@login_required
@require_http_methods(["POST"])
def member_remove(
    request: HttpRequest, username: str, slug: str, user_pk: int
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    target = get_membership(project=project, user_pk=user_pk)

    if not can_manage_member(request.user, target, project):
        return HttpResponseForbidden("Недостаточно прав")

    actor_membership = get_membership(request.user, project)
    try:
        removed_username = remove_member(
            actor_membership=actor_membership,
            target_membership=target,
        )
    except ValidationError as e:
        message_error(request, str(e))
        return _render_members_tab(request, project)

    message_success(request, f"{removed_username} удалён из проекта")
    return _render_members_tab(request, project)
