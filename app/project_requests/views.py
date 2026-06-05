from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from project_members.permissions import can_handle_requests, can_access_project
from projects.selectors import get_project

from .constants import RequestStatus
from .selectors import (
    get_requests_for_project,
    get_request_by_pk,
    get_request_comments,
    get_requests_by_author,
)
from .services import (
    add_comment,
    convert_request_to_task,
    create_request,
    decline_request,
    delete_request,
    update_request_status,
)


def _get_requests_queryset(project, user):
    """Return appropriate request queryset based on user permissions."""
    if can_handle_requests(user, project):
        return get_requests_for_project(project)
    return get_requests_by_author(project, author=user)


def _render_requests_tab(
    request: HttpRequest,
    project,
    *,
    template: str = "requests/partials/_requests_tab.html",
) -> HttpResponse:
    """Render requests tab partial with project and request list."""
    context = {
        "project": project,
        "requests": _get_requests_queryset(project, request.user),
        "is_tech_support": can_handle_requests(request.user, project),
    }
    return render(request, template, context)


@login_required
def request_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Main requests tab view."""
    project = get_project(username=username, slug=slug)

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Вы не участник проекта")

    if request.headers.get("HX-Request"):
        return _render_requests_tab(request, project)

    context = {
        "project": project,
        "requests": _get_requests_queryset(project, request.user),
        "is_tech_support": can_handle_requests(request.user, project),
        "tab": "requests",
    }
    return render(request, "projects/project_detail.html", context)


@login_required
@require_http_methods(["POST"])
def request_create(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Handle creation of new request."""
    project = get_project(username=username, slug=slug)

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Нет доступа")

    description = request.POST.get("description", "").strip()
    if not description:
        messages.error(request, "Введите описание")
        return _render_requests_tab(request, project)

    create_request(project=project, author=request.user, description=description)
    messages.success(request, "Запрос отправлен")
    return _render_requests_tab(request, project)


@login_required
def request_detail(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Detail view of request."""
    req = get_request_by_pk(pk=request_pk)

    if req.author != request.user and not can_handle_requests(
        request.user, req.project
    ):
        return HttpResponseForbidden("Нет доступа")

    return render(
        request,
        "requests/request_detail.html",
        {
            "project": req.project,
            "req": req,
            "messages_list": get_request_comments(req),
            "is_tech_support": can_handle_requests(request.user, req.project),
        },
    )


@login_required
def request_convert(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Convert request into task."""
    req = get_request_by_pk(pk=request_pk)

    if not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")

    task = convert_request_to_task(req=req, actor=request.user)
    messages.success(request, f"Задача «{task.name}» создана!")
    return redirect("project_tasks:task_detail", task_pk=task.pk)


@login_required
@require_http_methods(["POST"])
def request_delete(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Delete request ."""
    req = get_request_by_pk(pk=request_pk)

    if req.author != request.user:
        return HttpResponseForbidden("Вы не автор запроса")
    if req.status != RequestStatus.PENDING:
        return HttpResponse("Запрос уже обработан, нельзя удалить", status=400)

    project = req.project
    delete_request(req=req)

    messages.success(request, "Запрос удалён")
    response = HttpResponse(status=204)
    response["HX-Redirect"] = reverse(
        "project_requests:requests_tab",
        kwargs={"username": project.owner.username, "slug": project.slug},
    )
    return response


@login_required
@require_http_methods(["POST"])
def request_decline(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Decline pending request."""
    req = get_request_by_pk(pk=request_pk)

    if not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")
    if req.status != RequestStatus.PENDING:
        return HttpResponse("Запрос уже обработан", status=400)

    decline_request(req=req)
    messages.success(request, "Запрос отклонён")
    return redirect("project_requests:request_detail", request_pk=req.pk)


@login_required
@require_http_methods(["POST"])
def request_message_add(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Add comment to request, optionally changing status to reviewed."""
    req = get_request_by_pk(pk=request_pk)

    if req.author != request.user and not can_handle_requests(
        request.user, req.project
    ):
        return HttpResponseForbidden("Нет доступа к этому запросу")

    text = request.POST.get("text", "").strip()
    if text:
        add_comment(req=req, author=request.user, text=text)

        if (
            can_handle_requests(request.user, req.project)
            and req.status == RequestStatus.PENDING
        ):
            update_request_status(req=req, status=RequestStatus.REVIEWED)

    return render(
        request,
        "requests/partials/_request_messages_list.html",
        {
            "req": req,
            "messages_list": get_request_comments(req),
        },
    )


@login_required
def request_create_form(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Render the request creation form partial."""
    project = get_project(username=username, slug=slug)

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Нет доступа")

    return render(
        request,
        "requests/partials/_request_create_form.html",
        {"project": project},
    )


@login_required
@require_http_methods(["POST"])
def request_create_submit(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Handle request creation from dedicated form."""
    project = get_project(username=username, slug=slug)

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Нет доступа")

    description = request.POST.get("description", "").strip()
    if description:
        create_request(project=project, author=request.user, description=description)
        messages.success(request, "Запрос создан")

    return _render_requests_tab(request, project)
