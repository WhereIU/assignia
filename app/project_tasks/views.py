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
    is_user_assigned_to_task,
)
from .services import (
    apply_tasks_filters,
    create_task,
    update_task,
    delete_task,
    take_task,
    add_task_comment,
    assign_user_to_task,
    remove_user_from_task,
    add_direction_to_task,
    remove_direction_from_task,
    add_team_to_task,
    remove_team_from_task,
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
@require_http_methods(["GET", "POST"])
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
            "tasks/partials/_task_create_form.html",
            {"form": form, "project": project, **get_form_choices_context()},
            status=422
        )

    form = TaskCreateForm()
    return render(
        request,
        "tasks/partials/_task_create_form.html",
        {"form": form, "project": project, **get_form_choices_context()},
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
    
    privileged_user = is_privileged(request.user, task.project)
    
    is_assignee = is_user_assigned_to_task(task, request.user)

    if request.headers.get("HX-Target") == "messages-list-wrapper":
        return render(request, "tasks/partials/_task_comments_list.html", context)

    context.update({
        "project": task.project,
        "is_privileged": privileged_user,
        "is_assignee": is_assignee,
        "status_choices": TaskStatus.choices,
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
        
    if task.status == TaskStatus.DONE or task.is_deleted:
        return HttpResponse("Нельзя взять выполненную или удаленную задачу", status=400)

    if is_user_assigned_to_task(task, request.user):
        return HttpResponse("Вы уже взяли эту задачу", status=400)

    take_task(task=task, user=request.user)

    return render(
        request,
        "tasks/partials/_task_card.html",
        {
            "task": task,
            "is_privileged": is_privileged(request.user, task.project),
            "is_assignee": True,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def task_edit(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Edit task data."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    if request.method == "POST":
        is_full_form = "name" in request.POST
        if is_full_form:
            form = TaskCreateForm(request.POST, instance=task)
            if form.is_valid():
                update_task(task=task, data=request.POST)
                message_success(request, "Изменения сохранены")
                
                is_assignee = task.assignments.filter(user=request.user).exists()
                return render(
                    request,
                    "tasks/partials/_task_card.html",
                    {
                        "task": task,
                        "is_assignee": is_assignee,
                        "is_privileged": True,
                        "project_members": get_project_memberships(task.project),
                        "status_choices": TaskStatus.choices,
                    },
                )
            
            return render(
                request,
                "tasks/partials/_task_edit_form.html",
                {
                    "form": form, 
                    "task": task, 
                    "project": task.project, 
                    "status_choices": TaskStatus.choices,
                    **get_form_choices_context()
                },
                status=422
            )
        else:
            update_task(task=task, data=request.POST)
            
            is_assignee = task.assignments.filter(user=request.user).exists()
            return render(
                request,
                "tasks/partials/_task_card.html",
                {
                    "task": task,
                    "is_assignee": is_assignee,
                    "is_privileged": True,
                    "status_choices": TaskStatus.choices,
                },
            )

    form = TaskCreateForm(instance=task)
    return render(
        request,
        "tasks/partials/_task_edit_form.html",
        {
            "form": form,
            "task": task,
            "project": task.project,
            "status_choices": TaskStatus.choices,
            **get_form_choices_context()
        },
    )


@login_required
@require_http_methods(["POST"])
def task_delete(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Permanently delete task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    project = task.project
    if not is_privileged(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")

    delete_task(task=task)

    message_success(request, f"Задача «{task.name}» удалена безвозвратно")

    project_url = reverse(
        "projects:project_detail", 
        kwargs={"username": project.owner.username, "slug": project.slug}
    )
    redirect_url = f"{project_url}?tab=tasks"
    
    response = HttpResponse(status=200)
    response["HX-Redirect"] = redirect_url
    return response


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
    """Search members for task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("assignee_search", "").strip()
    members = get_project_memberships(task.project)
    
    if query:
        members = members.filter(user__username__icontains=query)
    
    already_assigned_ids = task.assignments.values_list('user_id', flat=True)
    members = members.exclude(user_id__in=already_assigned_ids)[:10]

    return render(
        request,
        "tasks/partials/_search_results.html",
        {"members": members, "task": task},
    )


@login_required
def task_direction_search(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Search directions for task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("direction_search", "").strip()
    directions = task.project.directions.filter(is_deleted=False)
    
    if query:
        directions = directions.filter(name__icontains=query)
        
    directions = directions.exclude(id__in=task.directions.values_list('id', flat=True))[:10]

    return render(
        request,
        "tasks/partials/_search_results.html",
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
    """Seach teams for task."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")

    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    query = request.GET.get("team_search", "").strip()
    teams = get_teams_by_project(task.project, is_deleted=False)
    
    if query:
        teams = teams.filter(name__icontains=query)
        
    teams = teams.exclude(id__in=task.teams.values_list('id', flat=True))[:10]

    return render(
        request,
        "tasks/partials/_search_results.html",
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


@login_required
def task_delete_confirm(request: HttpRequest, task_pk: int) -> HttpResponse:
    """Render soft-delete confirmation."""
    task = get_task_by_pk(pk=task_pk)
    if not task:
        raise Http404("Задача не найдена")
        
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    return render(
        request,
        "tasks/partials/_task_delete_confirm.html",
        {"task": task},
    )
