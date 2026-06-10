from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from project_members.permissions import can_manage_directions
from projects.selectors import get_project
from common.services import message_success, message_error
from common.selectors import get_paginated_page

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
    *,
    show_deleted: bool = False,
    can_manage: bool = False,
) -> HttpResponse:
    """Render directions tab."""
    template = (
        "directions/partials/_directions_list.html"
        if request.headers.get("HX-Target") == "directions-list-wrapper"
        else "directions/partials/_directions_tab.html"
    )
    
    search_query = request.GET.get("search", "").strip()
    page = request.GET.get("page", 1)

    directions_queryset = get_directions_by_project(project, is_deleted=show_deleted)
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
            "can_manage": can_manage,
            "show_deleted": show_deleted,
            "search_query": search_query,
        }
    )


@login_required
def directions_tab(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Return directions tab."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    show_deleted = request.GET.get("show_deleted") == "1"
    return _render_directions_tab(
        request,
        project,
        username,
        slug,
        show_deleted=show_deleted,
        can_manage=True,
    )


@login_required
@require_http_methods(["POST"])
def direction_create(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    form = DirectionForm(request.POST)

    if not form.is_valid():
        message_error(request, "Исправьте ошибки в форме")
        return render(
            request,
            "directions/partials/_direction_create_form.html",
            {
                "username": username,
                "slug": slug,
                "form": form,
            },
            status=422,
        )

    create_direction(
        project=project, 
        user=request.user, 
        name=form.cleaned_data['name'], 
        description=form.cleaned_data['description']
    )
    message_success(request, f"Направление «{form.cleaned_data['name']}» создано")
    
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def direction_update(request: HttpRequest, direction_pk: int) -> HttpResponse:
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")

    project = direction.project
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    form = DirectionForm(request.POST, instance=direction)

    if not form.is_valid():
        message_error(request, "Исправьте ошибки в форме")
        return render(
            request,
            "directions/partials/_direction_edit_form.html",
            {
                "direction": direction,
                "form": form,
            },
            status=422,
        )

    update_direction(
        direction=direction, 
        name=form.cleaned_data['name'], 
        description=form.cleaned_data['description']
    )
    message_success(request, "Направление успешно обновлено")
    
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def direction_delete(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Soft-delete direction."""
    direction = get_direction_by_pk(pk=direction_pk)
    if not direction:
        raise Http404("Направление не найдено")

    if not can_manage_directions(request.user, direction.project):
        return HttpResponseForbidden("Недостаточно прав")

    soft_delete_direction(direction=direction)

    message_success(request, f"Направление «{direction.name}» удалено")
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def direction_restore(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Restore soft-deleted direction."""
    direction = get_direction_by_pk(pk=direction_pk)
    if not direction:
        raise Http404("Направление не найдено")

    if not can_manage_directions(request.user, direction.project):
        return HttpResponseForbidden("Недостаточно прав")

    restore_direction(direction=direction)

    message_success(request, f"Направление «{direction.name}» восстановлено")
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def direction_hard_delete(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Permanently delete direction."""
    direction = get_direction_by_pk(pk=direction_pk)
    if not direction:
        raise Http404("Направление не найдено")

    project = direction.project
    name = direction.name
    if not can_manage_directions(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    hard_delete_direction(direction=direction)

    message_success(request, f"Направление «{name}» удалено безвозвратно")
    response = HttpResponse(status=200)
    response["HX-Trigger"] = "directionsChanged"
    return response


@login_required
def direction_create_form(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return form creating direction."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    form = DirectionForm()
    return render(
        request,
        "directions/partials/_direction_create_form.html",
        {
            "username": username,
            "slug": slug,
            "form": form,
        },
    )


@login_required
def direction_edit_form(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Return form editing direction."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")

    form = DirectionForm(instance=direction)
    return render(
        request,
        "directions/partials/_direction_edit_form.html",
        {
            "direction": direction,
            "form": form,
        },
    )


@login_required
def direction_delete_confirm(request: HttpRequest, direction_pk: int) -> HttpResponse:
    """Render soft-delete confirmation for direction."""
    direction = get_direction_by_pk(pk=direction_pk, is_deleted=False)
    if not direction:
        raise Http404("Направление не найдено")
        
    if not can_manage_directions(request.user, direction.project):
        return HttpResponseForbidden("Недостаточно прав")

    return render(
        request,
        "directions/partials/_direction_delete_confirm.html",
        {"direction": direction},
    )
