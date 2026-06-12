from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from projects.selectors import get_project
from common.services import message_success, message_error
from common.selectors import get_paginated_page

from .permissions import ProjectDirectionsPermissions
from .selectors import filter_directions_by_search, get_direction_by_pk, get_directions_by_project
from .services import (
    create_direction,
    update_direction,
    soft_delete_direction,
    restore_direction,
    hard_delete_direction,
)
from .forms import DirectionForm


def _render_directions_tab(
    request: HttpRequest,
    project,
    username: str,
    slug: str,
    perms: ProjectDirectionsPermissions,
    *,
    show_deleted: bool = False,
) -> HttpResponse:
    """Render tab container."""
    template = (
        "directions/partials/_directions_list.html"
        if request.headers.get("HX-Target") == "directions-list-wrapper"
        else "directions/partials/_directions_tab.html"
    )
    
    search_query = request.GET.get("search", "").strip()
    page = request.GET.get("page", 1)

    view_deleted = show_deleted if perms.can_manage_directions else False

    directions_queryset = get_directions_by_project(project, is_deleted=view_deleted)
    directions_queryset = filter_directions_by_search(directions_queryset, search_query)
    
    page_obj = get_paginated_page(
        queryset=directions_queryset,
        per_page=12,
        page=page,
    )
    
    return render(
        request,
        template,
        {
            "project": project,
            "username": username,
            "slug": slug,
            "page_obj": page_obj,
            "can_manage": perms.can_manage_directions,
            "show_deleted": view_deleted,
            "search_query": search_query,
        }
    )


def directions_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return directions tab view."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectDirectionsPermissions(request.user, project)
    if not perms.can_view_directions:
        raise PermissionDenied("У вас нет доступа к направлениям этого проекта")

    show_deleted = request.GET.get("show_deleted") == "1"
    return _render_directions_tab(
        request,
        project,
        username,
        slug,
        perms=perms,
        show_deleted=show_deleted,
    )


@login_required
@require_http_methods(["POST"])
def direction_create(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project: raise Http404()
    perms = ProjectDirectionsPermissions(request.user, project)
    if not perms.can_manage_directions: raise PermissionDenied()

    form = DirectionForm(request.POST)
    if form.is_valid():
        create_direction(project=project, user=request.user, 
                         name=form.cleaned_data['name'], description=form.cleaned_data['description'])
        message_success(request, f"Направление «{form.cleaned_data['name']}» создано")
        
        response = HttpResponse(status=200)
        response["HX-Trigger"] = "directionsChanged"
        return response
    
    message_error(request, "Исправьте ошибки в форме")
    return render(request, "directions/partials/_direction_create_form.html", 
        {"username": username, "slug": slug, "form": form}, status=422)


@login_required
@require_http_methods(["POST"])
def direction_update(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction: raise Http404()
    perms = ProjectDirectionsPermissions(request.user, direction.project)
    if not perms.can_manage_directions: raise PermissionDenied()

    form = DirectionForm(request.POST, instance=direction)
    if form.is_valid():
        update_direction(direction=direction, name=form.cleaned_data['name'], description=form.cleaned_data['description'])
        message_success(request, "Направление успешно обновлено")
        
        response = HttpResponse(status=200)
        response["HX-Trigger"] = "directionsChanged"
        return response

    message_error(request, "Исправьте ошибки в форме")
    return render(request, "directions/partials/_direction_edit_form.html", 
            {"direction": direction, "form": form}, status=422)


@login_required
@require_http_methods(["POST"])
def direction_delete(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Soft-delete active direction."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")

    perms = ProjectDirectionsPermissions(request.user, direction.project)
    if not perms.can_manage_directions:
        raise PermissionDenied()

    soft_delete_direction(direction=direction)
    message_success(request, f"Направление «{direction.name}» перенесено в архив")
    
    response = HttpResponse(
        status=200
    )
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def direction_restore(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Restore soft-deleted direction back to project."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=True)
    if not direction:
        raise Http404("Удаленное направление не найдено")

    perms = ProjectDirectionsPermissions(request.user, direction.project)
    if not perms.can_manage_directions:
        raise PermissionDenied()

    restore_direction(direction=direction)
    message_success(request, f"Направление «{direction.name}» восстановлено")
    
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def direction_hard_delete(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Permanently delete direction."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=True)
    if not direction:
        raise Http404("Направление не найдено в архиве")

    perms = ProjectDirectionsPermissions(request.user, direction.project)
    if not perms.can_manage_directions:
        raise PermissionDenied()

    name = direction.name
    hard_delete_direction(direction=direction)
    message_success(request, f"Направление «{name}» удалено безвозвратно")
    
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
def direction_create_form(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return form of creating a direction."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectDirectionsPermissions(request.user, project)
    if not perms.can_manage_directions:
        raise PermissionDenied()

    return render(
        request,
        "directions/partials/_direction_create_form.html",
        {
            "username": username,
            "slug": slug,
            "form": DirectionForm(),
        },
    )


@login_required
def direction_edit_form(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Return form of editing an direction."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")

    perms = ProjectDirectionsPermissions(request.user, direction.project)
    if not perms.can_manage_directions:
        raise PermissionDenied()

    return render(
        request,
        "directions/partials/_direction_edit_form.html",
        {
            "direction": direction,
            "form": DirectionForm(instance=direction),
        },
    )


@login_required
def direction_delete_confirm(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Render confirmation for deletion."""
    direction = get_direction_by_pk(pk=direction_pk)
    if not direction:
        raise Http404("Направление не найдено")
        
    perms = ProjectDirectionsPermissions(request.user, direction.project)
    if not perms.can_manage_directions:
        raise PermissionDenied()

    return render(
        request,
        "directions/partials/_direction_delete_confirm.html",
        {"direction": direction},
    )