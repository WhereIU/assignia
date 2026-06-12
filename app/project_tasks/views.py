from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse

from common.selectors import get_page_filters, get_paginated_page
from common.services import message_success
from projects.selectors import get_project

from .forms import TaskCreateForm
from .permissions import ProjectTasksPermissions
from .selectors import (
    get_task_by_pk,
    get_tasks_by_project,
    get_task_comments_context,
    get_form_choices_context,
    get_task_status_choices,
    get_task_risk_choices,
    get_task_priority_choices,
    get_available_actions_for_task,
)
from .services import (
    apply_tasks_filters,
    create_task,
    update_task,
    delete_task,
    take_task,
)


def _render_tasks_tab(request: HttpRequest, project, perms: ProjectTasksPermissions) -> HttpResponse:
    """Render tasks tab component."""
    template = (
        "tasks/partials/_tasks_list.html"
        if request.headers.get("HX-Target") == "tasks-list-wrapper"
        else "tasks/partials/_tasks_tab.html"
    )

    tasks = get_tasks_by_project(project)
    filters = get_page_filters(request)
    tasks = apply_tasks_filters(tasks, filters)

    page = request.GET.get("page", 1)
    page_obj = get_paginated_page(tasks, page, per_page=10)

    return render(
        request,
        template,
        {
            "project": project,
            "page_obj": page_obj,
            "filters": filters,
            "status_choices": get_task_status_choices(),
            "priority_choices": get_task_priority_choices(),
            "risk_choices": get_task_risk_choices(),
            "can_create": perms.can_create_tasks,
        },
    )


@login_required
def tasks_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Tasks tab entry point."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectTasksPermissions(request.user, project)
    if not perms.can_view_tasks:
        raise PermissionDenied("Нет доступа к задачам проекта")

    return _render_tasks_tab(request, project, perms)


@login_required
@require_http_methods(["GET", "POST"])
def task_create(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Create a new task."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectTasksPermissions(request.user, project)
    if not perms.can_create_tasks:
        raise PermissionDenied("Вы не можете создавать задачи в этом проекте")

    if request.method == "POST":
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            create_task(
                form=form,
                project=project,
                creator=request.user,
                assignee_ids=request.POST.getlist("assignee_ids"),
            )
            message_success(request, "Задача успешно создана")
            
            response = HttpResponse(status=200)
            response["HX-Trigger"] = "tasksChanged"
            return response
            
        return render(
            request,
            "tasks/partials/_task_create_form.html",
            {"form": form, "project": project, **get_form_choices_context()},
            status=422
        )

    return render(
        request,
        "tasks/partials/_task_create_form.html",
        {"form": TaskCreateForm(), "project": project, **get_form_choices_context()},
    )


@login_required
def task_detail(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Task detail view."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_view_tasks:
        raise PermissionDenied("Нет доступа к деталям задачи")

    page = request.GET.get("page", 1)
    context = get_task_comments_context(task, page_number=page)
    actions = get_available_actions_for_task(task, request.user, perms)

    if request.headers.get("HX-Target") == "messages-list-wrapper":
        return render(request, "tasks/partials/_task_comments_list.html", context)

    context.update({
        "project": task.project,
        "actions": actions,
        "status_choices": get_task_status_choices(),
    })
    return render(request, "tasks/task_detail.html", context)


@login_required
@require_POST
def task_take(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Assign a user to a task and update status."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    actions = get_available_actions_for_task(task, request.user, perms)
    if not actions["can_take"]:
        raise PermissionDenied("Вы не можете взять эту задачу")

    take_task(task=task, user=request.user)
    actions = get_available_actions_for_task(task, request.user, perms)

    if "task-card-container" in request.headers.get("HX-Target", ""):
        return render(
            request,
            "tasks/partials/_task_card.html",
            {"task": task, "actions": actions},
        )
    
    return render(
        request,
        "tasks/partials/_task_item.html",
        {"task": task, "user": request.user, "actions": actions},
    )


@login_required
@require_http_methods(["GET", "POST"])
def task_edit(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Edit task attributes."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        raise PermissionDenied("Недостаточно прав для редактирования")

    if request.method == "POST":
        is_full_form = "name" in request.POST
        if is_full_form:
            form = TaskCreateForm(request.POST, instance=task)
            if form.is_valid():
                update_task(task, **form.cleaned_data)
                message_success(request, "Изменения сохранены")
                
                return render(
                    request,
                    "tasks/partials/_task_card.html",
                    {
                        "task": task,
                        "actions": get_available_actions_for_task(task, request.user, perms),
                        "status_choices": get_task_status_choices(),
                    },
                )
            
            return render(
                request,
                "tasks/partials/_task_edit_form.html",
                {"form": form, "task": task, "project": task.project, **get_form_choices_context()},
                status=422
            )
        else:
            update_task(task, **request.POST.dict())
            return render(
                request,
                "tasks/partials/_task_card.html",
                {
                    "task": task,
                    "actions": get_available_actions_for_task(task, request.user, perms),
                    "status_choices": get_task_status_choices(),
                },
            )

    form = TaskCreateForm(instance=task)
    return render(
        request,
        "tasks/partials/_task_edit_form.html",
        {"form": form, "task": task, "project": task.project, **get_form_choices_context()},
    )


@login_required
@require_http_methods(["POST"])
def task_delete(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Permanently delete task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        raise PermissionDenied("Недостаточно прав")

    project = task.project
    delete_task(task=task)
    message_success(request, f"Задача «{task.name}» удалена безвозвратно")

    project_url = reverse(
        "projects:project_detail", 
        kwargs={"username": project.owner.username, "slug": project.slug}
    )
    
    response = HttpResponse(status=200)
    response["HX-Redirect"] = f"{project_url}?tab=tasks"
    return response
