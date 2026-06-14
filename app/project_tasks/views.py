from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse

from common.selectors import get_page_filters, get_paginated_page
from common.services import message_error, message_success
from projects.selectors import get_project

from .forms import TaskCreateForm, TaskUpdateForm
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
    get_assignable_task_members,
    get_assignable_task_directions,
    get_assignable_task_teams,
)
from .services import (
    add_direction_to_task,
    add_task_comment,
    add_team_to_task,
    apply_tasks_filters,
    assign_user_to_task,
    create_task,
    remove_direction_from_task,
    remove_team_from_task,
    remove_user_from_task,
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

            response = HttpResponse("", status=200)
            response["HX-Trigger"] = "tasksChanged"
            return response

        message_error(request, "Исправьте поля ввода") 
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
            form = TaskUpdateForm(request.POST, instance=task)
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
            allowed_fields = ['status', 'priority', 'risk_chance', 'risk_impact']
            safe_data = {k: v for k, v in request.POST.items() if k in allowed_fields}
            
            update_task(task, **safe_data)
            
            return render(
                request,
                "tasks/partials/_task_card.html",
                {
                    "task": task,
                    "actions": get_available_actions_for_task(task, request.user, perms),
                    "status_choices": get_task_status_choices(),
                },
            )

    form = TaskUpdateForm(instance=task)
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


@login_required
@require_POST
def direction_add_to_task(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add direction to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        return HttpResponseForbidden("Недостаточно прав для управления задачей")

    direction_id = request.POST.get("direction_id")
    if direction_id:
        error = add_direction_to_task(task=task, direction_id=int(direction_id))
        if error:
            return HttpResponse(error, status=400)

    response = render(
        request,
        "tasks/partials/_selected_directions.html",
        {"task": task},
    )
    response["HX-Trigger"] = "taskComponentsChanged"
    return response


@login_required
@require_POST
def direction_remove_from_task(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Remove direction from task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        return HttpResponseForbidden("Недостаточно прав для управления задачей")

    direction_id = request.POST.get("direction_id")
    if direction_id:
        remove_direction_from_task(task=task, direction_id=int(direction_id))

    response = render(
        request,
        "tasks/partials/_selected_directions.html",
        {"task": task},
    )
    response["HX-Trigger"] = "taskComponentsChanged"
    return response


@login_required
@require_POST
def team_add_to_task(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add team to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        return HttpResponseForbidden("Недостаточно прав для управления задачей")

    team_id = request.POST.get("team_id")
    if team_id:
        error = add_team_to_task(task=task, team_id=int(team_id))
        if error:
            return HttpResponse(error, status=400)

    response = render(
        request,
        "tasks/partials/_selected_teams.html",
        {"task": task},
    )
    response["HX-Trigger"] = "taskComponentsChanged"
    return response


@login_required
def task_delete_confirm(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Render task permanent deletion confirmation."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")
        
    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        raise PermissionDenied("Недостаточно прав")

    return render(
        request,
        "tasks/partials/_task_delete_confirm.html",
        {"task": task},
    )


@login_required
def task_member_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search project members for task assignment."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        raise PermissionDenied("Недостаточно прав")

    query = request.GET.get("assignee_search", "").strip()
    members = get_assignable_task_members(task, query)

    return render(
        request,
        "tasks/partials/_search_results.html",
        {"members": members, "task": task},
    )


@login_required
def task_direction_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search project directions for task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        raise PermissionDenied("Недостаточно прав")

    query = request.GET.get("direction_search", "").strip()
    directions = get_assignable_task_directions(task, query)

    return render(
        request,
        "tasks/partials/_search_results.html",
        {"directions": directions, "task": task},
    )


@login_required
def task_team_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search project teams for task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        raise PermissionDenied("Недостаточно прав")

    query = request.GET.get("team_search", "").strip()
    teams = get_assignable_task_teams(task, query)

    return render(
        request,
        "tasks/partials/_search_results.html",
        {"teams": teams, "task": task},
    )


@login_required
@require_POST
def team_remove_from_task(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Remove team from task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        return HttpResponseForbidden("Недостаточно прав для управления задачей")

    team_id = request.POST.get("team_id")
    if team_id:
        remove_team_from_task(task=task, team_id=int(team_id))

    response = render(
        request,
        "tasks/partials/_selected_teams.html",
        {"task": task},
    )
    response["HX-Trigger"] = "taskComponentsChanged"
    return response


@login_required
@require_POST
def assignee_add(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add assignee to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        return HttpResponseForbidden("Недостаточно прав для управления задачей")

    user_id = request.POST.get("user_id")
    if user_id:
        error = assign_user_to_task(task=task, user_id=int(user_id))
        if error:
            return HttpResponse(error, status=400)

    response = render(
        request,
        "tasks/partials/_selected_assignees.html",
        {"task": task},
    )
    response["HX-Trigger"] = "taskComponentsChanged"
    return response


@login_required
@require_POST
def assignee_remove(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Remove assignee from task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_manage_tasks:
        return HttpResponseForbidden("Недостаточно прав для управления задачей")

    user_id = request.POST.get("user_id")
    if user_id:
        remove_user_from_task(task=task, user_id=int(user_id))

    response = render(
        request,
        "tasks/partials/_selected_assignees.html",
        {"task": task},
    )
    response["HX-Trigger"] = "taskComponentsChanged"
    return response


@login_required
@require_http_methods(["POST"])
def task_comment_add(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add comment to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    perms = ProjectTasksPermissions(request.user, task.project)
    if not perms.can_view_tasks:
        raise PermissionDenied("Нет доступа к комментариям этой задачи")

    text = request.POST.get("text", "").strip()
    if text:
        add_task_comment(task=task, author=request.user, text=text)

    detail_path = reverse("project_tasks:task_detail", kwargs={"task_pk": task.pk})
    setattr(request, "path", detail_path)

    context = get_task_comments_context(task, page_number=1)
    
    return render(request, "tasks/partials/_task_comments_list.html", context)
