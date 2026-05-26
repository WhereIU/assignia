from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from projects.models import Project, ProjectMembership

from .models import Direction, Team


def can_manage_directions(user, project):
    if not user.is_authenticated:
        return False
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership and membership.role in ('admin', 'owner')


def can_manage_teams(user, direction):
    return can_manage_directions(user, direction.project)


def redirect_to_directions(request, project, show_deleted=False):
    directions = project.directions.filter(is_deleted=show_deleted).annotate(task_count=Count('tasks'))
    return render(request, 'directions/partials/_directions.html', {
        'project': project,
        'directions': directions,
        'can_manage': True,
        'show_deleted': show_deleted,
    })


def redirect_to_teams(request, direction):
    show_deleted = request.GET.get('show_deleted') == '1'
    teams = direction.teams.filter(is_deleted=show_deleted)
    return render(request, 'teams/partials/_teams.html', {
        'direction': direction,
        'project': direction.project,
        'teams': teams,
        'show_deleted': show_deleted,
    })


@login_required
def direction_tab(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    show_deleted = request.GET.get('show_deleted') == '1'
    return redirect_to_directions(request, project, show_deleted)


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
def direction_create(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    if not name:
        messages.error(request, 'Название направления обязательно')
        return redirect_to_directions(request, project)
    Direction.objects.create(project=project, name=name, description=description, created_by=request.user)
    messages.success(request, f'Направление «{name}» создано')
    return redirect_to_directions(request, project)


@login_required
@require_http_methods(["POST"])
def direction_update(request, direction_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=False)
    project = direction.project
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    if not name:
        messages.error(request, 'Название направления обязательно')
        return redirect_to_directions(request, project)
    direction.name = name
    direction.description = description
    direction.save()
    messages.success(request, 'Направление обновлено')
    return redirect_to_directions(request, project)


@login_required
@require_http_methods(["POST"])
def direction_delete(request, direction_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=False)
    project = direction.project
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    direction.is_deleted = True
    direction.save()
    messages.success(request, f'Направление «{direction.name}» удалено')
    return redirect_to_directions(request, project)


@login_required
@require_http_methods(["POST"])
def direction_restore(request, direction_pk):
    direction = get_object_or_404(Direction, pk=direction_pk, is_deleted=True)
    project = direction.project
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    direction.is_deleted = False
    direction.save()
    messages.success(request, f'Направление «{direction.name}» восстановлено')
    return redirect_to_directions(request, project, show_deleted=True)


@login_required
def direction_create_form(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    return render(request, 'directions/partials/_direction_form.html', {
        'project': project,
        'submit_url': reverse('directions:direction_create', kwargs={'username': username, 'slug': slug}),
    })


@login_required
def direction_edit_form(request, username, slug, direction_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    direction = get_object_or_404(Direction, pk=direction_pk, project=project, is_deleted=False)
    return render(request, 'directions/partials/_direction_form.html', {
        'project': project,
        'direction': direction,
        'submit_url': reverse('directions:direction_update', kwargs={'direction_pk': direction.pk}),
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
