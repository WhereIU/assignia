from __future__ import annotations
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import remove_member, update_member_role
from .permissions import ProjectRole, can_manage_member, is_admin_or_owner, is_privileged
from .selectors import (
    get_membership,
    get_membership_by_user_pk,
    get_member_role,
    get_project_memberships,
    search_project_memberships,
)

from projects.selectors import get_project, get_pending_invitations, filter_invitations_by_search
from common.services import message_success, message_error
from common.selectors import get_paginated_page

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
    memberships = list(
        search_project_memberships(project=project, query=search_query)
        if search_query
        else get_project_memberships(project=project)
    )
    
    invitations_qs = get_pending_invitations(project=project)
    invitations_qs = filter_invitations_by_search(invitations_qs, search_query)
    invitations = list(invitations_qs)
    
    members = invitations + memberships
    
    page_obj = get_paginated_page(members, page, 10)
    
    for member in page_obj:
        if hasattr(member, "sender"):
            member.can_manage = is_privileged(request.user, project)
        else:
            if member.user == request.user:
                member.can_manage = False
            else:
                member.can_manage = can_manage_member(request.user, member, project)

    actor_role = get_member_role(request.user, project)

    template = (
        "members/partials/_members_list.html"
        if request.headers.get("HX-Target") == "members-table-wrapper"
        else "members/partials/_members_tab.html"
    )

    return render(
        request,
        template,
        {
            "project": project,
            "members": page_obj,
            "actor_role": actor_role,
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
def members_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав для просмотра участников")
        
    search = request.GET.get("search", "")
    page = request.GET.get("page", 1)
    return _render_members_tab(request, project, search_query=search, page=page)


@login_required
@require_http_methods(["POST"])
def member_update_role(
    request: HttpRequest, username: str, slug: str, user_pk: int
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден в данном проекте")

    if not can_manage_member(request.user, target, project):
        return HttpResponseForbidden("У вас нет прав на редактирование этого участника")

    new_role = request.POST.get("role")
    if new_role not in ProjectRole.values:
        message_error(request, "Указана несуществующая роль")
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

    message_success(request, f"Роль {target.user.username} изменена на {target.get_role_display()}")
    return _render_members_tab(request, project)


@login_required
def member_update_role_form(request: HttpRequest, username: str, slug: str, user_pk: int) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден")

    if not can_manage_member(request.user, target, project):
        return HttpResponseForbidden("У вас нет прав на редактирование этого участника")

    return render(request, "members/partials/_member_update_role_form.html", {
        "project": project,
        "target": target,
        "roles": ProjectRole.choices,
    })


@login_required
@require_http_methods(["POST"])
def member_remove(
    request: HttpRequest, username: str, slug: str, user_pk: int
) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден в данном проекте")

    if not can_manage_member(request.user, target, project):
        return HttpResponseForbidden("У вас нет прав на удаление этого участника")

    actor_membership = get_membership(request.user, project)
    
    try:
        removed_username = remove_member(
            actor_membership=actor_membership,
            target_membership=target,
        )
    except ValidationError as e:
        message_error(request, str(e))
        return _render_members_tab(request, project)

    message_success(request, f"Пользователь {removed_username} успешно удалён из проекта")
    return _render_members_tab(request, project)


@login_required
def member_remove_confirm(request: HttpRequest, username: str, slug: str, user_pk: int) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    if not is_admin_or_owner(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден")

    return render(request, "members/partials/_member_remove_confirm.html", {
        "project": project,
        "target": target,
    })