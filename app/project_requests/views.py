from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from common.selectors import get_paginated_page
from common.services import message_success, message_error
from project_members.permissions import can_handle_requests, can_access_project
from projects.selectors import get_project

from .constants import RequestStatus
from .selectors import (
    get_filtered_requests_for_project,
    get_request_status_choices,
    get_request_by_pk,
    get_request_comments,
)
from .services import (
    add_comment,
    convert_request_to_task,
    create_request,
    decline_request,
    delete_request,
    update_request_status,
)
from .forms import TaskRequestForm


def _render_requests_tab(request: HttpRequest, project) -> HttpResponse:
    """Render requests tab."""
    if request.headers.get("HX-Target") == "requests-list-wrapper":
        template = "requests/partials/_requests_list.html"
    else:
        template = "requests/partials/_requests_tab.html"

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    page = request.GET.get("page", 1)

    requests_queryset = get_filtered_requests_for_project(
        project=project,
        user=request.user,
        search_query=search_query,
        status_filter=status_filter
    )

    page_obj = get_paginated_page(
        queryset=requests_queryset,
        per_page=10,
        page=page,
    )

    return render(
        request,
        template,
        {
            "project": project,
            "page_obj": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_choices": get_request_status_choices(),
        }
    )


@login_required
def requests_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Requests tab."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Нет доступа")

    return _render_requests_tab(request, project)


@login_required
@require_http_methods(["POST"])
def request_create(
    request: HttpRequest, username: str, slug: str
) -> HttpResponse:
    """Handle creation of new request."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Нет доступа")

    description = request.POST.get("description", "").strip()
    if not description:
        message_error(request, "Введите описание")
        return _render_requests_tab(request, project)

    create_request(project=project, author=request.user, description=description)
    message_success(request, "Запрос отправлен")
    return _render_requests_tab(request, project)


@login_required
def request_detail(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Detail view of request."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

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
    if not req:
        raise Http404("Запрос не найден")

    if not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")

    task = convert_request_to_task(req=req, actor=request.user)
    message_success(request, f"Задача «{task.name}» создана!")
    return render(request, "requests/partials/_request_card.html", {"req": req, "is_tech_support": True})


@login_required
@require_http_methods(["POST"])
def request_delete(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Delete request."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    if req.author != request.user:
        return HttpResponseForbidden("Вы не автор запроса")
    if req.status != RequestStatus.PENDING:
        return HttpResponse("Запрос уже обработан, нельзя удалить", status=400)

    project = req.project
    delete_request(req=req)

    message_success(request, "Запрос удалён")
    response = HttpResponse(status=200)
    response["HX-Redirect"] = f"/projects/{project.owner.username}/{project.slug}/?tab=requests"
    return response


@login_required
@require_http_methods(["POST"])
def request_decline(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Decline pending request."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    if not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")
    if req.status != RequestStatus.PENDING:
        return HttpResponse("Запрос уже обработан", status=400)

    decline_request(req=req)
    message_success(request, "Запрос отклонён")
    return render(request, "requests/partials/_request_card.html", {"req": req, "is_tech_support": True})


@login_required
@login_required
@require_http_methods(["POST"])
def request_message_add(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Add comment to request, optionally changing status to reviewed."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    if req.author != request.user and not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Нет доступа к этому запросу")

    text = request.POST.get("text", "").strip()
    if text:
        add_comment(req=req, author=request.user, text=text)

        if can_handle_requests(request.user, req.project) and req.status == RequestStatus.PENDING:
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
@require_http_methods(["GET", "POST"])
def request_create(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Create new request for tech support."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not can_access_project(request.user, project):
        return HttpResponseForbidden("Нет доступа")

    if request.method == "POST":
        form = TaskRequestForm(request.POST)
        if form.is_valid():
            create_request(
                project=project,
                author=request.user,
                description=form.cleaned_data["description"],
            )
            message_success(request, "Запрос в поддержку успешно создан")
            
            response = HttpResponse(status=200)
            response["HX-Trigger"] = "requestsChanged"
            return response
        
        message_error(request, "Исправьте ошибки в форме")
        return render(
            request,
            "requests/partials/_request_create_form.html",
            {
                "project": project,
                "form": form,
            },
            status=422,
        )

    form = TaskRequestForm()
    return render(
        request,
        "requests/partials/_request_create_form.html",
        {
            "project": project,
            "form": form,
        },
    )
