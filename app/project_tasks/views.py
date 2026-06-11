from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from common.selectors import get_page_filters
from common.services import message_success
from common.selectors import get_paginated_page 
from project_members.permissions import (
    is_privileged,
    is_project_member,
    can_delete_task_or_error,
)
from project_members.selectors import get_project_memberships
from project_teams.selectors import get_teams_by_project
from projects.selectors import get_project

from .constants import TaskStatus, PriorityLevel, RiskLevel
from .forms import TaskCreateForm
from .selectors import (
    get_task_by_pk,
    get_task_comments_context,
    get_tasks_by_project,
    get_form_choices_context,
)
from .services import (
    apply_tasks_filters,
    create_task,
    update_task,
    delete_task,
    restore_task,
    take_task,
    add_task_comment,
    assign_user_to_task,
    remove_user_from_task,
    add_direction_to_task,
    remove_direction_from_task,
    add_team_to_task,
    remove_team_from_task,
    update_task_status,
    update_task_priority,
    update_task_risk,
)


@login_required
def tasks_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Handle tasks tab."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not is_project_member(request.user, project):
        return HttpResponseForbidden("Нет доступа к задачам проекта")

    if request.headers.get("HX-Target") == "tasks-list-wrapper":
        template = "tasks/partials/_tasks_list.html"
    else:
        template = "tasks/partials/_tasks_tab.html"

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
            "status_choices": TaskStatus.choices,
            "priority_choices": PriorityLevel.choices,
        },
    )


@login_required
def task_create(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Create a new task."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not is_project_member(request.user, project):
        return HttpResponseForbidden("Вы не участник проекта")

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
            "tasks/partials/_task_form.html",
            {"form": form, "project": project, **get_form_choices_context()},
            status=422
        )

    return render(
        request,
        "tasks/partials/_task_form.html",
        {"project": project, **get_form_choices_context()},
    )


@login_required
def task_detail(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Task detail."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_project_member(request.user, task.project):
        return HttpResponseForbidden("Нет доступа")

    page = request.GET.get("page", 1)
    context = get_task_comments_context(task, page_number=page)

    if request.headers.get("HX-Target") == "messages-list-wrapper":
        return render(request, "tasks/partials/_task_comments_list.html", context)

    context.update({
        "project": task.project,
    })
    return render(request, "tasks/task_detail.html", context)


@login_required
@require_http_methods(["POST"])
def task_take(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Take task for execution."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_project_member(request.user, task.project):
        return HttpResponseForbidden("Вы не участник проекта")
    if task.status != TaskStatus.NEW or task.assignments.exists():
        return HttpResponse("Задача уже занята или не новая", status=400)

    take_task(task=task, user=request.user)

    return render(
        request,
        "tasks/partials/_task_item.html",
        {"task": task, "show_take_button": False},
    )


@login_required
def task_edit(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Handle edit task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    return render(
        request,
        "tasks/partials/_task_form.html",
        {
            "task": task,
            "project": task.project,
            **get_form_choices_context()
        },
    )

@login_required
@require_http_methods(["POST"])
def task_save(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Save changes of task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    update_task(
        task=task,
        data=request.POST,
        assignee_ids=request.POST.getlist("assignee_ids") if "assignee_ids" in request.POST else None,
    )
    message_success(request, "Изменения сохранены")

    return render(
        request,
        "tasks/partials/_task_view.html",
        {
            "task": task,
            "is_privileged": True,
            "project_members": get_project_memberships(task.project),
        },
    )


@login_required
@require_http_methods(["POST"])
def task_delete(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Soft-delete task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    error = can_delete_task_or_error(request.user, task)
    if error:
        return HttpResponse(error, status=400)

    delete_task(task=task)
    message_success(request, "Задача удалена")

    return render(
        request,
        "tasks/partials/_task_view.html",
        {
            "task": task,
            "is_privileged": is_privileged(request.user, task.project),
            "project_members": get_project_memberships(task.project),
        },
    )


@login_required
@require_http_methods(["POST"])
def task_restore(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Restore soft-deleted task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    restore_task(task=task)
    message_success(request, "Задача восстановлена")

    return render(
        request,
        "tasks/partials/_task_view.html",
        {
            "task": task,
            "is_privileged": True,
            "project_members": get_project_memberships(task.project),
        },
    )


@login_required
@require_http_methods(["POST"])
def task_update_status(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Update status of task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    new_status = request.POST.get("status")
    if new_status not in TaskStatus.values:
        return HttpResponse("Неверный статус", status=400)

    update_task_status(task=task, status=new_status)
    return render(request, "tasks/partials/_task_item.html", {"task": task})


@login_required
@require_http_methods(["POST"])
def task_update_priority(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Update priority of task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    try:
        new_priority = int(request.POST.get("priority"))
        if new_priority not in PriorityLevel.values:
            raise ValueError
    except (TypeError, ValueError):
        return HttpResponse("Неверный приоритет", status=400)

    update_task_priority(task=task, priority=new_priority)
    return render(request, "tasks/partials/_task_item.html", {"task": task})


@login_required
@require_http_methods(["POST"])
def task_update_risk(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Update risk chance and impact of task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    try:
        risk_chance = int(request.POST.get("risk_chance"))
        risk_impact = int(request.POST.get("risk_impact"))
        if (
            risk_chance not in RiskLevel.values
            or risk_impact not in RiskLevel.values
        ):
            raise ValueError
    except (TypeError, ValueError):
        return HttpResponse("Неверные значения рисков", status=400)

    update_task_risk(task=task, chance=risk_chance, impact=risk_impact)
    return render(request, "tasks/partials/_task_item.html", {"task": task})


@login_required
@require_http_methods(["POST"])
def task_comment_add(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add comment to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    text = request.POST.get("text", "").strip()
    if text:
        add_task_comment(task=task, author=request.user, text=text)

    detail_path = reverse("project_tasks:task_detail", kwargs={"task_pk": task.pk})
    setattr(request, "path", detail_path)

    context = get_task_comments_context(task, page_number=1)
    
    return render(request, "tasks/partials/_task_comments_list.html", context)


@login_required
@require_http_methods(["POST"])
def task_assignee_add(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add assignee to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    error = assign_user_to_task(task=task, user_id=request.POST.get("user_id"))
    if error:
        return HttpResponse(error, status=400)

    return render(
        request,
        "tasks/partials/_selected_assignees.html",
        {"task": task},
    )


@login_required
@require_http_methods(["POST"])
def task_assignee_remove(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Remove assignee from task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    remove_user_from_task(task=task, user_id=request.POST.get("user_id"))
    return render(
        request,
        "tasks/partials/_selected_assignees.html",
        {"task": task},
    )


@login_required
def task_member_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search project members for assignment."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("assignee_search", "").strip()
    members = get_project_memberships(task.project)
    if query:
        members = members.filter(user__username__icontains=query)[:10]

    return render(
        request,
        "projects/partials/_project_members_list.html",
        {"members": members, "task": task},
    )


@login_required
def task_direction_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search directions for the task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("direction_search", "").strip()
    directions = task.project.directions.filter(is_deleted=False)
    if query:
        directions = directions.filter(name__icontains=query)[:15]

    return render(
        request,
        "directions/partials/_directions_list.html",
        {"directions": directions, "task": task},
    )


@login_required
@require_http_methods(["POST"])
def task_direction_add(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add direction to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    error = add_direction_to_task(
        task=task, direction_id=request.POST.get("direction_id")
    )
    if error:
        return HttpResponse(error, status=400)

    return render(
        request,
        "directions/partials/_selected_directions.html",
        {"task": task},
    )


@login_required
@require_http_methods(["POST"])
def task_direction_remove(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Remove direction from task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    remove_direction_from_task(
        task=task, direction_id=request.POST.get("direction_id")
    )
    return render(
        request,
        "directions/partials/_selected_directions.html",
        {"task": task},
    )


@login_required
def task_team_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search teams for task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("team_search", "").strip()
    teams = get_teams_by_project(task.project, is_deleted=False)
    if query:
        teams = teams.filter(name__icontains=query)[:15]

    return render(
        request,
        "teams/partials/_teams_list.html",
        {"teams": teams, "task": task},
    )


@login_required
@require_http_methods(["POST"])
def task_team_add(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Add team to task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    error = add_team_to_task(task=task, team_id=request.POST.get("team_id"))
    if error:
        return HttpResponse(error, status=400)

    return render(
        request,
        "teams/partials/_selected_teams.html",
        {"task": task},
    )


@login_required
@require_http_methods(["POST"])
def task_team_remove(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Remove team from task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    remove_team_from_task(task=task, team_id=request.POST.get("team_id"))
    return render(
        request,
        "teams/partials/_selected_teams.html",
        {"task": task},
    )
