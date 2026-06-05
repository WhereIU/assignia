from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from project_members.permissions import can_manage_directions
from projects.selectors import get_project
from common.services import message_success, message_error

from .selectors import get_direction_by_pk, get_directions_by_project
from .services import (
    create_direction,
    update_direction,
    soft_delete_direction,
    restore_direction,
    hard_delete_direction,
)


def _render_directions_tab(
    request: HttpRequest,
    project,
    *,
    show_deleted: bool = False,
    can_manage: bool = False,
) -> HttpResponse:
    """Render directions tab partial."""
    return render(
        request,
        "directions/partials/_directions_tab.html",
        {
            "project": project,
            "directions": get_directions_by_project(project, is_deleted=show_deleted),
            "can_manage": can_manage,
            "show_deleted": show_deleted,
        },
    )


@login_required
def direction_tab(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Return directions tab."""
    project = get_project(username=username, slug=slug)
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    show_deleted = request.GET.get("show_deleted") == "1"
    return _render_directions_tab(
        request,
        project,
        show_deleted=show_deleted,
        can_manage=True,
    )


@login_required
@require_http_methods(["POST"])
def direction_create(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Handle direction creation."""
    project = get_project(username=username, slug=slug)
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not name:
        message_error(request, "Название направления обязательно")
        return _render_directions_tab(request, project, can_manage=True)

    create_direction(
        project=project,
        user=request.user,
        name=name,
        description=description,
    )

    message_success(request, f"Направление «{name}» создано")
    return _render_directions_tab(request, project, can_manage=True)


@login_required
@require_http_methods(["POST"])
def direction_update(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Handle direction update."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    project = direction.project
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not name:
        message_error(request, "Название направления обязательно")
        return _render_directions_tab(request, project, can_manage=True)

    update_direction(
        direction=direction,
        name=name,
        description=description,
    )

    message_success(request, "Направление обновлено")
    return _render_directions_tab(request, project, can_manage=True)


@login_required
@require_http_methods(["POST"])
def direction_delete(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Soft-delete direction."""
    direction = get_direction_by_pk(pk=direction_pk)
    if not can_manage_directions(request.user, direction.project):
        return HttpResponseForbidden("Недостаточно прав")

    soft_delete_direction(direction=direction)

    message_success(request, f"Направление «{direction.name}» удалено")
    return _render_directions_tab(request, direction.project, can_manage=True)


@login_required
@require_http_methods(["POST"])
def direction_restore(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Restore soft-deleted direction."""
    direction = get_direction_by_pk(pk=direction_pk)
    if not can_manage_directions(request.user, direction.project):
        return HttpResponseForbidden("Недостаточно прав")

    restore_direction(direction=direction)

    message_success(request, f"Направление «{direction.name}» восстановлено")
    return _render_directions_tab(
        request, direction.project, show_deleted=True, can_manage=True
    )


@login_required
@require_http_methods(["POST"])
def direction_hard_delete(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Permanently delete direction."""
    direction = get_direction_by_pk(pk=direction_pk)
    project = direction.project
    name = direction.name
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    hard_delete_direction(direction=direction)

    message_success(request, f"Направление «{name}» удалено безвозвратно")
    return _render_directions_tab(request, project, show_deleted=True, can_manage=True)


@login_required
def direction_create_form(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Return form partial for creating direction."""
    project = get_project(username=username, slug=slug)
    return render(
        request,
        "directions/partials/_direction_create_form.html",
        {
            "project": project,
            "submit_url": reverse(
                "project_directions:direction_create",
                kwargs={"username": username, "slug": slug},
            ),
        },
    )


@login_required
def direction_edit_form(
    request: HttpRequest, username: str, slug: str, direction_pk: int
) -> HttpResponse:
    """Return form partial for editing direction."""
    project = get_project(username=username, slug=slug)
    direction = get_direction_by_pk(pk=direction_pk)
    return render(
        request,
        "directions/partials/_direction_create_form.html",
        {
            "project": project,
            "direction": direction,
            "submit_url": reverse(
                "project_directions:direction_update",
                kwargs={"direction_pk": direction.pk},
            ),
        },
    )
