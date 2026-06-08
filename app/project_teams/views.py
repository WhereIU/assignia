from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from project_members.permissions import can_manage_teams
from project_members.selectors import search_project_memberships
from project_directions.selectors import get_direction_by_pk
from users.models import User
from common.services import message_success, message_error
from common.selectors import get_paginated_page

from .selectors import (
    filter_teams_by_search,
    get_team_by_pk,
    get_teams_by_direction,
    get_team_members,
)
from .services import (
    create_team,
    hard_delete_team,
    update_team,
    soft_delete_team,
    restore_team,
    add_member_to_team,
    remove_member_from_team,
)


def _render_teams_tab(
    request: HttpRequest, direction, show_deleted: bool =False
) -> HttpResponse:
    """Render teams tab."""

    search_query = request.GET.get("search", "").strip()
    page = request.GET.get("page", 1)

    teams_queryset = get_teams_by_direction(direction, is_deleted=show_deleted)
    
    teams_queryset = filter_teams_by_search(teams_queryset, search_query)

    page_obj = get_paginated_page(teams_queryset, page, per_page=12)
    
    context = {
        "direction": direction,
        "page_obj": page_obj,
        "show_deleted": show_deleted,
        "search_query": search_query,
    }

    if request.headers.get("HX-Target") == "teams-list-wrapper":
        return render(request, "teams/partials/_teams_list.html", context)
        
    return render(request, "teams/partials/_teams_tab.html", context)


@login_required
def teams_tab(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)

    if not direction:
        raise Http404("Направление не найдено")

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    
    show_deleted = request.GET.get("show_deleted") == "1"
    
    return _render_teams_tab(
        request, direction, show_deleted=show_deleted
    )


@login_required
@require_http_methods(["POST"])
def team_create(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    if not name:
        message_error(request, "Название команды обязательно")
        return render(
            request,
            "teams/partials/_team_create_edit_form.html",
            {
                "direction": direction,
                "project": direction.project,
                "submit_url": reverse("project_teams:team_create", kwargs={"direction_pk": direction_pk}),
            },
            status=422
        )

    create_team(direction=direction, name=name)
    message_success(request, f"Команда «{name}» создана")

    response = HttpResponse(status=200)
    response["HX-Trigger"] = "teamsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def team_update(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")
        
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    if not name:
        message_error(request, "Название команды обязательно")
        return render(
            request,
            "teams/partials/_team_create_edit_form.html",
            {
                "direction": direction,
                "project": direction.project,
                "team": team,
                "submit_url": reverse("project_teams:team_update", kwargs={"team_pk": team_pk}),
            },
            status=422
        )

    update_team(team=team, name=name)
    message_success(request, "Команда обновлена")
    
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "teamsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def team_delete(request: HttpRequest, team_pk: int) -> HttpResponse:
    """Soft-delete team."""
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")
        
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    soft_delete_team(team=team)
    message_success(request, f"Команда «{team.name}» удалена")
    
    response = HttpResponse("")
    response["HX-Trigger"] = "teamsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def team_hard_delete(request: HttpRequest, team_pk: int) -> HttpResponse:
    """Permanently delete team."""
    team = get_team_by_pk(pk=team_pk, is_deleted=True)
    if not team:
        raise Http404("Команда не найдена")
        
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    team_name = team.name
    hard_delete_team(team=team)
    message_success(request, f"Команда «{team_name}» полностью удалена")
    
    response = HttpResponse("")
    response["HX-Trigger"] = "teamsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def team_restore(request: HttpRequest, team_pk: int) -> HttpResponse:
    """Restore soft-deleted team."""
    team = get_team_by_pk(pk=team_pk, is_deleted=True)
    if not team:
        raise Http404("Команда не найдена")
        
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    restore_team(team=team)
    message_success(request, f"Команда «{team.name}» восстановлена")
    
    response = HttpResponse("")
    response["HX-Trigger"] = "teamsChanged"
    return response


@login_required
def team_members(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")

    if not can_manage_teams(request.user, team.direction):
        return HttpResponseForbidden("Недостаточно прав")

    members = get_team_members(team)
    return render(
        request,
        "members/partials/_team_members.html",
        {
            "team": team,
            "members": members,
            "direction": team.direction,
            "project": team.direction.project,
        },
    )


@login_required
def team_member_search(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")

    if not can_manage_teams(request.user, team.direction):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("member_search", "").strip()
    members = search_project_memberships(team.direction.project, query)

    return render(
        request,
        "teams/partials/_team_member_search_results.html",
        {"members": members, "team": team},
    )


@login_required
@require_http_methods(["POST"])
def team_member_add(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")
        
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    user_id = request.POST.get("user_id")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return HttpResponse("Пользователь не найден", status=404)

    try:
        add_member_to_team(team=team, user=user)
    except ValueError as e:
        return HttpResponse(str(e), status=400)

    members = get_team_members(team)
    return render(
        request,
        "teams/partials/_team_members.html",
        {
            "team": team,
            "members": members,
            "direction": direction,
            "project": direction.project,
        },
    )


@login_required
@require_http_methods(["POST"])
def team_member_remove(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")
        
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    user_id = request.POST.get("user_id")
    user = User.objects.filter(pk=user_id).first()
    
    if user:
        remove_member_from_team(team=team, user=user)

    members = get_team_members(team)
    return render(
        request,
        "members/partials/_team_members.html",
        {
            "team": team,
            "members": members,
            "direction": direction,
            "project": direction.project,
        },
    )


@login_required
def team_create_form(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")

    return render(
        request,
        "teams/partials/_team_create_edit_form.html",
        {
            "direction": direction,
            "project": direction.project,
            "submit_url": reverse(
                "project_teams:team_create",
                kwargs={"direction_pk": direction_pk},
            ),
        },
    )


@login_required
def team_edit_form(
    request: HttpRequest, direction_pk: int, team_pk: int
) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")
        
    team = get_team_by_pk(pk=team_pk)
    if not team:
        raise Http404("Команда не найдена")

    return render(
        request,
        "teams/partials/_team_create_edit_form.html",
        {
            "direction": direction,
            "project": direction.project,
            "team": team,
            "submit_url": reverse(
                "project_teams:team_update",
                kwargs={"team_pk": team_pk},
            ),
        },
    )


@login_required
def team_delete_confirm_form(request: HttpRequest, team_pk: int) -> HttpResponse:
    """Render soft-delete form."""
    team = get_team_by_pk(pk=team_pk, is_deleted=False)
    if not team:
        raise Http404("Команда не найдена")
        
    if not can_manage_teams(request.user, team.direction):
        return HttpResponseForbidden("Недостаточно прав")

    return render(
        request,
        "teams/partials/_team_delete_confirm.html",
        {
            "team": team,
            "submit_url": reverse("project_teams:team_delete", kwargs={"team_pk": team.pk}),
        },
    )
