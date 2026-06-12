from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from common.selectors import get_paginated_page
from common.services import message_success, message_error
from projects.selectors import get_project

from .permissions import ProjectRequestsPermissions
from .selectors import (
    get_available_actions_for_request,
    get_filtered_requests_for_project,
    get_request_status_choices,
    get_request_by_pk,
    get_messages_context,
    is_request_pending,
)
from .services import (
    add_message,
    convert_request_to_task,
    create_request,
    decline_request,
    delete_request,
)
from .forms import TaskRequestForm


def _render_requests_tab(
    request: HttpRequest, project, perms: ProjectRequestsPermissions
) -> HttpResponse:
    """Render requests tab component."""
    template = (
        "requests/partials/_requests_list.html"
        if request.headers.get("HX-Target") == "requests-list-wrapper"
        else "requests/partials/_requests_tab.html"
    )

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    page = request.GET.get("page", 1)

    requests_queryset = get_filtered_requests_for_project(
        project=project,
        user=request.user,
        perms=perms,
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
            "can_handle": perms.can_handle_requests,
        }
    )


@login_required
def requests_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Requests tab entry point."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectRequestsPermissions(request.user, project)
    if not perms.can_view_requests:
        raise PermissionDenied("Нет доступа к запросам этого проекта")

    return _render_requests_tab(request, project, perms)


@login_required
@require_http_methods(["GET", "POST"])
def request_create(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Create new request."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectRequestsPermissions(request.user, project)
    if not perms.can_create_requests:
        raise PermissionDenied()

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
            {"project": project, "form": form},
            status=422,
        )

    return render(
        request,
        "requests/partials/_request_create_form.html",
        {"project": project, "form": TaskRequestForm()},
    )


@login_required
def request_detail(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Render full request detail."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    perms = ProjectRequestsPermissions(request.user, req.project)
    
    if req.author != request.user and not perms.can_handle_requests:
        raise PermissionDenied("Нет доступа к деталям запроса")

    page = request.GET.get("page", 1)
    context = get_messages_context(req, page_number=page)

    if request.headers.get("HX-Target") == "messages-list-wrapper":
        return render(request, "requests/partials/_request_messages_list.html", context)

    context.update({
        "project": req.project,
        "actions": get_available_actions_for_request(req, request.user, perms),
        "is_tech_support": perms.can_handle_requests,
    })
    return render(request, "requests/request_detail.html", context)


@login_required
@require_http_methods(["POST"])
def request_convert(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Convert active request into a task."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    perms = ProjectRequestsPermissions(request.user, req.project)
    if not perms.can_handle_requests:
        raise PermissionDenied("Недостаточно прав для конвертации")

    if not is_request_pending(req):
        return HttpResponse("Запрос уже обработан", status=400)

    convert_request_to_task(req=req, actor=request.user)
    message_success(request, "Запрос успешно конвертирован в задачу!")
    
    return render(
        request,
        "requests/partials/_request_card.html",
        {"req": req, "is_tech_support": True}
    )


@login_required
@require_http_methods(["POST"])
def request_decline(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Decline user request by support staff."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    perms = ProjectRequestsPermissions(request.user, req.project)
    if not perms.can_handle_requests:
        raise PermissionDenied("Недостаточно прав для отклонения")

    if not is_request_pending(req):
        return HttpResponse("Запрос уже обработан", status=400)

    decline_request(req=req)
    message_success(request, "Запрос отклонён")
    
    return render(
        request,
        "requests/partials/_request_card.html",
        {"req": req, "is_tech_support": True}
    )


@login_required
@require_http_methods(["POST"])
def request_delete(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Delete request."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    if req.author != request.user:
        raise PermissionDenied("Вы не являетесь автором этого запроса")
        
    if not is_request_pending(req):
        return HttpResponse("Запрос уже обработан техподдержкой, его нельзя удалить", status=400)

    project = req.project
    delete_request(req=req)
    message_success(request, "Запрос успешно удалён")
    
    response = HttpResponse(status=200)
    project_url = reverse("projects:project_detail", kwargs={"username": project.owner.username, "slug": project.slug})
    response["HX-Redirect"] = f"{project_url}?tab=requests"
    return response


@login_required
@require_http_methods(["POST"])
def request_message_add(request: HttpRequest, request_pk: int) -> HttpResponse:
    """Add text message to request."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    perms = ProjectRequestsPermissions(request.user, req.project)
    if req.author != request.user and not perms.can_handle_requests:
        raise PermissionDenied()

    text = request.POST.get("text", "").strip()
    if text:
        add_message(req=req, author=request.user, text=text)

    detail_path = reverse("project_requests:request_detail", kwargs={"request_pk": req.pk})
    setattr(request, "path", detail_path)

    context = get_messages_context(req, page_number=1)
    return render(request, "requests/partials/_request_messages_list.html", context)


@login_required
def request_action_confirm(request: HttpRequest, request_pk: int, action_type: str) -> HttpResponse:
    """Render action confirmation."""
    req = get_request_by_pk(pk=request_pk)
    if not req:
        raise Http404("Запрос не найден")

    perms = ProjectRequestsPermissions(request.user, req.project)
    actions = get_available_actions_for_request(req, request.user, perms)

    if action_type == "convert" and not actions["can_convert"]:
        raise PermissionDenied("Нет доступа к конвертации запроса")
    elif action_type == "decline" and not actions["can_decline"]:
        raise PermissionDenied("Нет доступа к отклонению запроса")
    elif action_type == "delete" and not actions["can_delete"]:
        raise PermissionDenied("Вы не можете удалить данный запрос")
    elif action_type not in ["convert", "decline", "delete"]:
        raise Http404("Неизвестный тип действия")

    return render(
        request,
        "requests/partials/_action_confirm.html",
        {"req": req, "action_type": action_type},
    )
