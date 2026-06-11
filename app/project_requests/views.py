from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from common.selectors import get_paginated_page
from common.services import message_success, message_error
from project_members.permissions import can_handle_requests, can_access_project
from projects.selectors import get_project

from .constants import RequestStatus
from .selectors import (
    get_filtered_requests_for_project,
    get_request_status_choices,
    get_request_by_pk,
    get_messages_context,
)
from .services import (
    add_message,
    convert_request_to_task,
    create_request,
    decline_request,
    delete_request,
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
    req = get_request_by_pk(pk=request_pk)
    if not req or (req.author != request.user and not can_handle_requests(request.user, req.project)):
        return HttpResponseForbidden("Нет доступа")

    page = request.GET.get("page", 1)
    context = get_messages_context(req, page_number=page)

    if request.headers.get("HX-Target") == "messages-list-wrapper":
        return render(request, "requests/partials/_request_messages_list.html", context)

    context.update({
        "project": req.project,
        "is_tech_support": can_handle_requests(request.user, req.project),
    })
    return render(request, "requests/request_detail.html", context)


@login_required
@require_http_methods(["POST"])
def request_convert(request: HttpRequest, request_pk: int) -> HttpResponse:
    req = get_request_by_pk(pk=request_pk)
    if not req or not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")

    convert_request_to_task(req=req, actor=request.user)
    message_success(request, "Запрос успешно конвертирован в задачу!")
    
    return render(
        request,
        "requests/partials/_request_card.html",
        {
            "req": req,
            "is_tech_support": True,
        }
    )


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
    
    project_url = reverse("projects:project_detail", kwargs={"username": project.owner.username, "slug": project.slug})
    response["HX-Redirect"] = f"{project_url}?tab=requests"
    
    return response


@login_required
@require_http_methods(["POST"])
def request_decline(request: HttpRequest, request_pk: int) -> HttpResponse:
    req = get_request_by_pk(pk=request_pk)
    if not req or not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")

    decline_request(req=req)
    message_success(request, "Запрос отклонён")
    
    return render(
        request,
        "requests/partials/_request_card.html",
        {
            "req": req,
            "is_tech_support": True,
        }
    )


@login_required
@require_http_methods(["POST"])
def request_message_add(request: HttpRequest, request_pk: int) -> HttpResponse:
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404()

    text = request.POST.get("text", "").strip()
    if text:
        add_message(req=req, author=request.user, text=text)

    detail_path = reverse("project_requests:request_detail", kwargs={"request_pk": req.pk})
    
    setattr(request, "path", detail_path)

    context = get_messages_context(req, page_number=1)
    
    return render(request, "requests/partials/_request_messages_list.html", context)


@login_required
def request_action_confirm(request: HttpRequest, request_pk: int, action_type: str) -> HttpResponse:
    """Render action confirm."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    if action_type in ["convert", "decline"]:
        if not can_handle_requests(request.user, req.project):
            return HttpResponseForbidden("Нет доступа")
    elif action_type == "delete":
        if req.author != request.user:
            return HttpResponseForbidden("Вы не автор запроса")
    else:
        raise Http404("Неизвестное действие")

    return render(
        request,
        "requests/partials/_action_confirm.html",
        {
            "req": req,
            "action_type": action_type,
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
