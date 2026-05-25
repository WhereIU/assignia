from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from projects.models import Project, ProjectMembership

from .models import Direction


def can_manage_directions(user, project):
    if not user.is_authenticated:
        return False
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership and membership.role in ('admin', 'owner')


def redirect_to_directions(request, project, show_deleted=False):
    directions = project.directions.filter(is_deleted=show_deleted).annotate(task_count=Count('tasks'))
    return render(request, 'divisions/partials/_directions.html', {
        'project': project,
        'directions': directions,
        'can_manage': True,
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
    return render(request, 'divisions/partials/_direction_form.html', {
        'project': project,
        'submit_url': reverse('directions:direction_create', kwargs={'username': username, 'slug': slug}),
    })


@login_required
def direction_edit_form(request, username, slug, direction_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    direction = get_object_or_404(Direction, pk=direction_pk, project=project, is_deleted=False)
    return render(request, 'divisions/partials/_direction_form.html', {
        'project': project,
        'direction': direction,
        'submit_url': reverse('directions:direction_update', kwargs={'direction_pk': direction.pk}),
    })
