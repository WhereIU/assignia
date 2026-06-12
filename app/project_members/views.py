from __future__ import annotations
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import remove_member, update_member_role
from .permissions import ProjectMembersPermissions
from .selectors import (
    get_membership_by_user_pk,
    get_project_memberships,
    search_project_memberships,
    get_assignable_roles_for_user,
)
from .forms import MemberRoleForm

from projects.selectors import get_project, get_pending_invitations, filter_invitations_by_search
from common.services import message_success, message_error
from common.selectors import get_paginated_page

if TYPE_CHECKING:
    from projects.models import Project


def _render_members_tab(
    request: HttpRequest,
    project: Project,
    perms: ProjectMembersPermissions,
    *,
    search_query: str = "",
    page: int = 1,
) -> HttpResponse:
    """Render members tab component."""
    memberships = list(
        search_project_memberships(project=project, query=search_query)
        if search_query
        else get_project_memberships(project=project)
    )
    
    invitations_qs = get_pending_invitations(project=project)
    invitations_qs = filter_invitations_by_search(invitations_qs, search_query)
    invitations = list(invitations_qs)
    
    combined_members = invitations + memberships
    page_obj = get_paginated_page(combined_members, page, 10)
    

    if perms.can_manage_members:
        for item in page_obj:
            if hasattr(item, "sender"):
                item.can_manage = True
            else:
                item.can_manage = perms.can_edit_member(item)
    else:
        for item in page_obj:
            item.can_manage = False

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
            "page_obj": page_obj,
            "search_query": search_query,
            "available_roles": get_assignable_roles_for_user(perms),
            "perms": {
                "can_manage_members": perms.can_manage_members,
            }
        },
    )


@login_required
def members_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Entry point view for rendering the project members tab."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    perms = ProjectMembersPermissions(request.user, project)
    if not perms.can_view_members:
        raise PermissionDenied("Недостаточно прав для просмотра участников")
        
    search = request.GET.get("search", "")
    page = request.GET.get("page", 1)
    return _render_members_tab(request, project, perms, search_query=search, page=page)


@login_required
@require_http_methods(["POST"])
def member_update_role(
    request: HttpRequest, username: str, slug: str, user_pk: int
) -> HttpResponse:
    """Update role for a specific member."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден в данном проекте")

    perms = ProjectMembersPermissions(request.user, project)
    if not perms.can_edit_member(target):
        raise PermissionDenied("У вас нет прав на редактирование этого участника")

    form = MemberRoleForm(request.POST, instance=target, perms=perms)
    if not form.is_valid():
        message_error(request, "Указана несуществующая роль")
        return _render_members_tab(request, project, perms)
    
    try:
        update_member_role(
            target_membership=target,
            new_role=form.cleaned_data['role'],
        )
    except ValidationError as e:
        form.add_error('role', e.message)
        message_error(request, str(e))
        return render(
            request, 
            "members/partials/_member_update_role_form.html", 
            {
                "project": project,
                "target": target,
                "form": form,
            },
            status=422
        )

    message_success(request, f"Роль {target.user.username} изменена на {target.get_role_display()}")
    return _render_members_tab(request, project, perms)


@login_required
def member_update_role_form(request: HttpRequest, username: str, slug: str, user_pk: int) -> HttpResponse:
    """Get partial form for updating a member's role."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден")

    perms = ProjectMembersPermissions(request.user, project)
    if not perms.can_edit_member(target):
        raise PermissionDenied("У вас нет прав на редактирование этого участника")

    form = MemberRoleForm(instance=target, perms=perms)
    return render(request, "members/partials/_member_update_role_form.html", {
        "project": project,
        "target": target,
        "form": form,
    })


@login_required
@require_http_methods(["POST"])
def member_remove(
    request: HttpRequest, username: str, slug: str, user_pk: int
) -> HttpResponse:
    """Remove a member from the project."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден в данном проекте")

    perms = ProjectMembersPermissions(request.user, project)
    if not perms.can_edit_member(target):
        raise PermissionDenied("У вас нет прав на удаление этого участника")
    
    try:
        removed_username = remove_member(target_membership=target)
    except ValidationError as e:
        message_error(request, str(e))
        return _render_members_tab(request, project, perms)

    message_success(request, f"Пользователь {removed_username} успешно удалён из проекта")
    return _render_members_tab(request, project, perms)


@login_required
def member_remove_confirm(request: HttpRequest, username: str, slug: str, user_pk: int) -> HttpResponse:
    """Get partial confirmation before removing a member."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")
        
    target = get_membership_by_user_pk(project=project, user_pk=user_pk)
    if not target:
        raise Http404("Участник не найден")

    perms = ProjectMembersPermissions(request.user, project)
    if not perms.can_edit_member(target):
        raise PermissionDenied("Недостаточно прав")

    return render(request, "members/partials/_member_remove_confirm.html", {
        "project": project,
        "target": target,
    })
