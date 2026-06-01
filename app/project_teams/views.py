from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from users.models import User
from project_directions.models import Direction
from project_directions.views import can_manage_directions
from projects.models import ProjectMembership

from .models import Team


@login_required
def team_tab(request, direction_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=False)
    project = direction.project
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    show_deleted = request.GET.get('show_deleted') == '1'
    teams = direction.teams.filter(is_deleted=show_deleted)
    return render(request, 'teams/partials/_teams.html', {
        'direction': direction,
        'project': project,
        'teams': teams,
        'show_deleted': show_deleted,
    })


@login_required
@require_http_methods(["POST"])
def team_create(request, direction_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=False)
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Название команды обязательно')
        return redirect_to_teams(request, direction)
    Team.objects.create(direction=direction, name=name)
    messages.success(request, f'Команда «{name}» создана')
    return redirect_to_teams(request, direction)


@login_required
@require_http_methods(["POST"])
def team_update(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Название команды обязательно')
        return redirect_to_teams(request, direction)
    team.name = name
    team.save()
    messages.success(request, 'Команда обновлена')
    return redirect_to_teams(request, direction)


@login_required
@require_http_methods(["POST"])
def team_delete(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    team.is_deleted = True
    team.save()
    messages.success(request, f'Команда «{team.name}» удалена')
    return redirect_to_teams(request, direction)


@login_required
@require_http_methods(["POST"])
def team_restore(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk, is_deleted=True)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    team.is_deleted = False
    team.save()
    messages.success(request, f'Команда «{team.name}» восстановлена')
    return redirect_to_teams(request, direction)


@login_required
def team_members(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    members = team.members.all()
    return render(request, 'teams/partials/_team_members.html', {
        'team': team,
        'members': members,
        'direction': direction,
        'project': direction.project,
    })


@login_required
def team_member_search(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    query = request.GET.get('member_search', '').strip()
    members = ProjectMembership.objects.filter(project=direction.project).select_related('user')
    if query:
        members = members.filter(user__username__icontains=query)[:10]
    else:
        members = members.all()[:10]
    return render(request, 'teams/partials/_team_member_search_results.html', {
        'members': members,
        'team': team,
    })


@login_required
@require_http_methods(["POST"])
def team_member_add(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    user_id = request.POST.get('user_id')
    try:
        user = User.objects.get(pk=user_id)
        if not ProjectMembership.objects.filter(user=user, project=direction.project).exists():
            return HttpResponse("Пользователь не участник проекта", status=400)
        team.members.add(user)
    except User.DoesNotExist:
        return HttpResponse("Пользователь не найден", status=404)
    members = team.members.all()
    return render(request, 'teams/partials/_team_members.html', {
        'team': team,
        'members': members,
        'direction': direction,
        'project': direction.project,
    })


@login_required
@require_http_methods(["POST"])
def team_member_remove(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    direction = team.direction
    if not can_manage_teams(request.user, direction):
        return HttpResponseForbidden("Недостаточно прав")
    user_id = request.POST.get('user_id')
    try:
        user = User.objects.get(pk=user_id)
        team.members.remove(user)
    except User.DoesNotExist:
        pass
    members = team.members.all()
    return render(request, 'teams/partials/_team_members.html', {
        'team': team,
        'members': members,
        'direction': direction,
        'project': direction.project,
    })


@login_required
def team_create_form(request, direction_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=False)
    return render(request, 'teams/partials/_team_form.html', {
        'direction': direction,
        'project': direction.project,
        'submit_url': reverse('teams:team_create', kwargs={'direction_pk': direction_pk}),
    })


@login_required
def team_edit_form(request, direction_pk, team_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=False)
    team = get_object_or_404(Team, pk=team_pk, direction=direction)
    return render(request, 'teams/partials/_team_form.html', {
        'direction': direction,
        'project': direction.project,
        'team': team,
        'submit_url': reverse('teams:team_update', kwargs={'team_pk': team_pk}),
    })


def can_manage_teams(user, direction):
    return can_manage_directions(user, direction.project)


def redirect_to_teams(request, direction):
    show_deleted = request.GET.get('show_deleted') == '1'
    teams = direction.teams.filter(is_deleted=show_deleted)
    return render(request, 'teams/partials/_teams.html', {
        'direction': direction,
        'project': direction.project,
        'teams': teams,
        'show_deleted': show_deleted,
    })
