from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from project_members.permissions import can_manage_teams
from project_members.selectors import search_project_memberships
from project_directions.selectors import get_direction_by_pk
from users.models import User

from .selectors import (
    get_team_by_pk,
    get_teams_by_direction,
    get_team_members,
)
from .services import (
    create_team,
    update_team,
    soft_delete_team,
    restore_team,
    add_member_to_team,
    remove_member_from_team,
)


def _render_teams_tab(
    request: HttpRequest, direction, *, show_deleted: bool = False
) -> HttpResponse:
    """Render the full teams tab for a direction."""
    teams = get_teams_by_direction(direction, is_deleted=show_deleted)
    return render(
        request,
        "teams/partials/_teams_tab.html",
        {
            "direction": direction,
            "project": direction.project,
            "teams": teams,
            "show_deleted": show_deleted,
        },
    )


@login_required
def team_tab(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    show_deleted = request.GET.get("show_deleted") == "1"
    return _render_teams_tab(request, direction, show_deleted=show_deleted)


@login_required
@require_http_methods(["POST"])
def team_create(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Название команды обязательно")
        return _render_teams_tab(request, direction)

    create_team(direction=direction, name=name)
    messages.success(request, f"Команда «{name}» создана")
    return _render_teams_tab(request, direction)


@login_required
@require_http_methods(["POST"])
def team_update(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Название команды обязательно")
        return _render_teams_tab(request, direction)

    update_team(team=team, name=name)
    messages.success(request, "Команда обновлена")
    return _render_teams_tab(request, direction)


@login_required
@require_http_methods(["POST"])
def team_delete(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    soft_delete_team(team=team)
    messages.success(request, f"Команда «{team.name}» удалена")
    return _render_teams_tab(request, direction)


@login_required
@require_http_methods(["POST"])
def team_restore(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk, is_deleted=True)
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    restore_team(team=team)
    messages.success(request, f"Команда «{team.name}» восстановлена")
    return _render_teams_tab(request, direction, show_deleted=True)


@login_required
def team_members(request: HttpRequest, team_pk: int) -> HttpResponse:
    team = get_team_by_pk(pk=team_pk)

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
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    user_id = request.POST.get("user_id")
    try:
        user = User.objects.get(pk=user_id)
        add_member_to_team(team=team, user=user)
    except User.DoesNotExist:
        return HttpResponse("Пользователь не найден", status=404)
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
    direction = team.direction

    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")

    user_id = request.POST.get("user_id")
    try:
        user = User.objects.get(pk=user_id)
        remove_member_from_team(team=team, user=user)
    except User.DoesNotExist:
        pass  # already not a member, fine

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
    team = get_team_by_pk(pk=team_pk)

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