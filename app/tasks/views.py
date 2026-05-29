from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from divisions.models import Direction, Team
from projects.models import Project, ProjectMembership
from users.models import User
from core.models import Notification

from .forms import TaskCreateForm
from .models import Comment, RequestMessage, Task, TaskAssignment, TaskRequest


def get_project_or_404(username, slug):
    return get_object_or_404(Project, owner__username=username, slug=slug)


def check_project_access(user, project):
    if project.is_public:
        return True
    return user.is_authenticated and ProjectMembership.objects.filter(user=user, project=project).exists()


def is_privileged(user, project):
    if not user.is_authenticated:
        return False
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership and membership.role in ('manager', 'admin', 'owner')


def can_handle_requests(user, project):
    if not user.is_authenticated:
        return False
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership and membership.role in ('tech_support', 'manager', 'admin', 'owner')


@login_required
def tasks_tab(request, username, slug):
    project = get_project_or_404(username, slug)
    tasks = Task.objects.filter(project=project, is_deleted=False)

    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    risk = request.GET.get('risk', '')
    q = request.GET.get('q', '')

    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=int(priority))
    if risk == 'high':
        tasks = tasks.filter(Q(risk_chance__gte=4) | Q(risk_impact__gte=4))
    elif risk == 'low':
        tasks = tasks.filter(risk_chance__lte=3, risk_impact__lte=3)
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))

    tasks = tasks.order_by('-priority', '-created_at')

    return render(request, 'tasks/partials/_task_list.html', {
        'tasks': tasks,
        'show_take_button': True,
        'filters': {'status': status, 'priority': str(priority) if priority else '', 'risk': risk, 'q': q},
        'target_id': 'tab-content',
    })


@login_required
def task_create(request, username, slug):
    project = get_project_or_404(username, slug)
    if not ProjectMembership.objects.filter(user=request.user, project=project).exists():
        return HttpResponseForbidden("Вы не участник проекта")

    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.creator = request.user
            task.save()
            assignee_ids = request.POST.getlist('assignee_ids')
            if assignee_ids:
                for user_id in assignee_ids:
                    try:
                        user = User.objects.get(pk=user_id)
                        if ProjectMembership.objects.filter(user=user, project=project).exists():
                            TaskAssignment.objects.create(task=task, user=user)
                    except User.DoesNotExist:
                        pass
            messages.success(request, f'Задача «{task.title}» создана!')
            return redirect('projects:project_detail', username=username, slug=slug)
    else:
        form = TaskCreateForm()

    return render(request, 'tasks/task_create.html', {'form': form, 'project': project})


def task_detail(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    project = task.project

    if not check_project_access(request.user, project):
        return HttpResponseForbidden("У вас нет доступа к этой задаче")

    comments = task.comments.order_by('-created_at')
    context = {
        'task': task,
        'project': project,
        'comments': comments,
        'is_privileged': is_privileged(request.user, project),
    }
    if context['is_privileged']:
        context['project_members'] = ProjectMembership.objects.filter(project=project).select_related('user')

    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_take(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not ProjectMembership.objects.filter(user=request.user, project=task.project).exists():
        return HttpResponseForbidden("Вы не участник проекта")
    if task.status != 'new' or task.assignments.exists():
        return HttpResponse("Задача уже занята или не новая", status=400)

    TaskAssignment.objects.create(task=task, user=request.user)
    task.status = 'in_progress'
    task.save()
    return render(request, 'tasks/partials/_task_item.html', {'task': task, 'show_take_button': False})


@login_required
def task_edit(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    project_members = ProjectMembership.objects.filter(project=task.project).select_related('user')
    return render(request, 'tasks/partials/_task_edit.html', {
        'task': task,
        'project': task.project,
        'project_members': project_members,
    })


@login_required
@require_http_methods(["POST"])
def task_save(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    task.title = request.POST.get('title', task.title)
    task.status = request.POST.get('status', task.status)
    task.priority = int(request.POST.get('priority', task.priority))
    task.risk_chance = int(request.POST.get('risk_chance', task.risk_chance))
    task.risk_impact = int(request.POST.get('risk_impact', task.risk_impact))
    task.description = request.POST.get('description', task.description)
    deadline = request.POST.get('deadline')
    task.deadline = deadline if deadline else None

    assignee_ids = request.POST.getlist('assignee_ids')
    if assignee_ids:
        task.assignments.exclude(user__pk__in=assignee_ids).delete()
        for user_id in assignee_ids:
            try:
                user = User.objects.get(pk=user_id)
                if ProjectMembership.objects.filter(user=user, project=task.project).exists():
                    TaskAssignment.objects.get_or_create(task=task, user=user)
            except User.DoesNotExist:
                pass
    else:
        task.assignments.all().delete()

    task.save()
    messages.success(request, 'Задача сохранена')
    return render(request, 'tasks/partials/_task_view.html', {
        'task': task,
        'is_privileged': True,
        'project_members': ProjectMembership.objects.filter(project=task.project).select_related('user'),
    })


@login_required
@require_http_methods(["POST"])
def task_delete(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    membership = ProjectMembership.objects.filter(user=request.user, project=task.project).first()
    if not membership:
        return HttpResponseForbidden("Вы не участник проекта")
    if membership.role == 'participant':
        if task.creator != request.user:
            return HttpResponseForbidden("Вы не автор задачи")
        if task.status not in ('new', 'pending') or task.assignments.exists():
            return HttpResponse("Нельзя удалить эту задачу", status=400)
    elif not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")

    task.is_deleted = True
    task.save()
    messages.success(request, 'Задача удалена')
    return render(request, 'tasks/partials/_task_view.html', {
        'task': task,
        'is_privileged': is_privileged(request.user, task.project),
        'project_members': ProjectMembership.objects.filter(project=task.project).select_related('user'),
    })


@login_required
@require_http_methods(["POST"])
def task_restore(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    task.is_deleted = False
    task.save()
    messages.success(request, 'Задача восстановлена')
    return render(request, 'tasks/partials/_task_view.html', {
        'task': task,
        'is_privileged': True,
        'project_members': ProjectMembership.objects.filter(project=task.project).select_related('user'),
    })


@login_required
@require_http_methods(["POST"])
def task_update_status(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    new_status = request.POST.get('status')
    if new_status not in dict(Task.STATUS_CHOICES):
        return HttpResponse("Неверный статус", status=400)
    task.status = new_status
    task.save()
    return render(request, 'tasks/partials/_task_item.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def task_update_priority(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    try:
        new_priority = int(request.POST.get('priority'))
        if new_priority not in range(1, 6):
            raise ValueError
    except (TypeError, ValueError):
        return HttpResponse("Неверный приоритет", status=400)
    task.priority = new_priority
    task.save()
    return render(request, 'tasks/partials/_task_item.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def task_update_risk(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    try:
        risk_chance = int(request.POST.get('risk_chance'))
        risk_impact = int(request.POST.get('risk_impact'))
        if risk_chance not in range(1, 6) or risk_impact not in range(1, 6):
            raise ValueError
    except (TypeError, ValueError):
        return HttpResponse("Неверные значения рисков", status=400)
    task.risk_chance = risk_chance
    task.risk_impact = risk_impact
    task.save()
    return render(request, 'tasks/partials/_task_item.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def comment_add(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    text = request.POST.get('text', '').strip()
    if text:
        Comment.objects.create(task=task, author=request.user, text=text)
    comments = task.comments.order_by('-created_at')
    return render(request, 'common/partials/_comments.html', {'task': task, 'comments': comments})


@login_required
@require_http_methods(["POST"])
def assignee_add(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    user_id = request.POST.get('user_id')
    try:
        user = User.objects.get(pk=user_id)
        if not ProjectMembership.objects.filter(user=user, project=task.project).exists():
            return HttpResponse("Пользователь не участник проекта", status=400)
        TaskAssignment.objects.get_or_create(task=task, user=user)
    except User.DoesNotExist:
        return HttpResponse("Пользователь не найден", status=404)
    return render(request, 'common/partials/_selected_assignees.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def assignee_remove(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    user_id = request.POST.get('user_id')
    try:
        user = User.objects.get(pk=user_id)
        TaskAssignment.objects.filter(task=task, user=user).delete()
    except User.DoesNotExist:
        pass
    return render(request, 'common/partials/_selected_assignees.html', {'task': task})


@login_required
def member_search(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    query = request.GET.get('assignee_search', '').strip()
    members = ProjectMembership.objects.filter(project=task.project).select_related('user')
    if query:
        members = members.filter(user__username__icontains=query)[:10]
    return render(request, 'common/partials/_member_list.html', {'members': members, 'task': task})


@login_required
def direction_search(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    query = request.GET.get('direction_search', '').strip()
    directions = task.project.directions.filter(is_deleted=False)
    if query:
        directions = directions.filter(name__icontains=query)[:15]
    else:
        directions = directions.all()[:15]
    return render(request, 'common/partials/_direction_list.html', {'directions': directions, 'task': task})


@login_required
def team_search(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    query = request.GET.get('team_search', '').strip()
    teams = Team.objects.filter(direction__project=task.project, is_deleted=False).distinct()
    if query:
        teams = teams.filter(name__icontains=query)[:15]
    else:
        teams = teams.all()[:15]
    return render(request, 'common/partials/_team_list.html', {'teams': teams, 'task': task})


@login_required
@require_http_methods(["POST"])
def direction_add_to_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    direction_id = request.POST.get('direction_id')
    try:
        direction = Direction.objects.get(pk=direction_id, project=task.project, is_deleted=False)
        task.directions.add(direction)
    except Direction.DoesNotExist:
        return HttpResponse("Направление не найдено", status=404)
    return render(request, 'common/partials/_selected_directions.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def direction_remove_from_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    direction_id = request.POST.get('direction_id')
    try:
        direction = Direction.objects.get(pk=direction_id, project=task.project)
        task.directions.remove(direction)
    except Direction.DoesNotExist:
        pass
    return render(request, 'common/partials/_selected_directions.html', {'task': task})


@login_required
def request_tab(request, username, slug):
    project = get_project_or_404(username, slug)
    if not project.is_public and not ProjectMembership.objects.filter(user=request.user, project=project).exists():
        return HttpResponseForbidden("Вы не участник проекта")

    if can_handle_requests(request.user, project):
        requests_qs = TaskRequest.objects.filter(project=project).order_by('-created_at')
    else:
        requests_qs = TaskRequest.objects.filter(project=project, author=request.user).order_by('-created_at')

    context = {'project': project, 'requests': requests_qs, 'is_tech_support': can_handle_requests(request.user, project)}
    if request.headers.get('HX-Request'):
        return render(request, 'requests/partials/_requests.html', context)
    return render(request, 'projects/project_detail.html', {**context, 'tab': 'requests'})


@login_required
def request_create(request, username, slug):
    project = get_project_or_404(username, slug)
    if not check_project_access(request.user, project):
        return HttpResponseForbidden("Вы не можете оставлять запросы в этом проекте")
    description = request.POST.get('description', '').strip()
    if description:
        TaskRequest.objects.create(project=project, author=request.user, description=description)
        messages.success(request, 'Запрос отправлен')
    else:
        messages.error(request, 'Введите описание')
    if can_handle_requests(request.user, project):
        requests_qs = TaskRequest.objects.filter(project=project).order_by('-created_at')
    else:
        requests_qs = TaskRequest.objects.filter(project=project, author=request.user).order_by('-created_at')
    return render(request, 'requests/partials/_requests.html', {
        'project': project,
        'requests': requests_qs,
        'is_tech_support': can_handle_requests(request.user, project),
    })


@login_required
def request_detail(request, request_pk):
    req = get_object_or_404(TaskRequest, pk=request_pk)
    project = req.project
    if req.author != request.user and not can_handle_requests(request.user, project):
        return HttpResponseForbidden("Нет доступа к этому запросу")
    messages_list = req.messages.order_by('created_at')
    return render(request, 'requests/request_detail.html', {
        'project': project,
        'req': req,
        'messages_list': messages_list,
        'is_tech_support': can_handle_requests(request.user, project),
    })


#@require_http_methods(["POST"])
@login_required
def request_convert(request, request_pk):
    req = get_object_or_404(TaskRequest, pk=request_pk)
    project = req.project
    if not can_handle_requests(request.user, project):
        return HttpResponseForbidden("Недостаточно прав")
    task = Task.objects.create(
        project=project,
        title=f"Запрос от {req.author.username}: {req.description[:50]}",
        description=req.description,
        creator=request.user,
        priority=2,
    )
    req.status = 'converted'
    req.save()
    messages.success(request, f'Задача «{task.title}» создана!')
    return redirect('tasks:task_detail', task_pk=task.pk)


@login_required
@require_http_methods(["POST"])
def request_delete(request, request_pk):
    req = get_object_or_404(TaskRequest, pk=request_pk)
    if req.author != request.user:
        return HttpResponseForbidden("Вы не автор запроса")
    if req.status != 'pending':
        return HttpResponse("Запрос уже обработан, нельзя удалить", status=400)
    req.delete()
    messages.success(request, 'Запрос удалён')
    redirect_url = reverse('requests:requests_tab', kwargs={'username': req.project.owner.username, 'slug': req.project.slug})
    response = HttpResponse(status=204)
    response['HX-Redirect'] = redirect_url
    return response


@login_required
@require_http_methods(["POST"])
def request_decline(request, request_pk):
    req = get_object_or_404(TaskRequest, pk=request_pk)
    if not can_handle_requests(request.user, req.project):
        return HttpResponseForbidden("Недостаточно прав")
    if req.status != 'pending':
        return HttpResponse("Запрос уже обработан", status=400)
    req.status = 'declined'
    req.save()
    Notification.objects.create(
        recipient=req.author,
        text=f'Ваш запрос в проекте «{req.project.name}» отклонён',
        url=reverse('requests:request_detail', kwargs={'request_pk': req.pk})
    )
    messages.success(request, 'Запрос отклонён')
    return redirect('requests:request_detail', request_pk=req.pk)


@login_required
def request_message_add(request, request_pk):
    req = get_object_or_404(TaskRequest, pk=request_pk)
    project = req.project
    if req.author != request.user and not can_handle_requests(request.user, project):
        return HttpResponseForbidden("Нет доступа к этому запросу")
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            RequestMessage.objects.create(request=req, author=request.user, text=text)
            if can_handle_requests(request.user, project) and req.status == 'pending':
                req.status = 'reviewed'
                req.save()
    messages_list = req.messages.order_by('created_at')
    return render(request, 'requests/partials/_request_messages.html', {
        'req': req,
        'messages_list': messages_list,
    })


@login_required
def request_create_form(request, username, slug):
    project = get_project_or_404(username, slug)
    if not project.is_public:
        if not ProjectMembership.objects.filter(user=request.user, project=project).exists():
            return HttpResponseForbidden("Вы не участник проекта")
    return render(request, 'requests/partials/_request_create_form.html', {'project': project})


@login_required
@require_http_methods(["POST"])
def request_create_submit(request, username, slug):
    project = get_project_or_404(username, slug)
    if not project.is_public:
        if not ProjectMembership.objects.filter(user=request.user, project=project).exists():
            return HttpResponseForbidden("Вы не участник проекта")
    description = request.POST.get('description', '').strip()
    if description:
        TaskRequest.objects.create(project=project, author=request.user, description=description)
        messages.success(request, 'Запрос создан')
    if can_handle_requests(request.user, project):
        requests_qs = TaskRequest.objects.filter(project=project).order_by('-created_at')
    else:
        requests_qs = TaskRequest.objects.filter(project=project, author=request.user).order_by('-created_at')
    context = {'project': project, 'requests': requests_qs, 'is_tech_support': can_handle_requests(request.user, project)}
    return render(request, 'requests/partials/_requests.html', context)


@login_required
@require_http_methods(["POST"])
def team_add_to_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    team_id = request.POST.get('team_id')
    try:
        team = Team.objects.get(pk=team_id, direction__project=task.project, is_deleted=False)
        task.teams.add(team)
    except Team.DoesNotExist:
        return HttpResponse("Команда не найдена", status=404)
    return render(request, 'common/partials/_selected_teams.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def team_remove_from_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    team_id = request.POST.get('team_id')
    try:
        team = Team.objects.get(pk=team_id, direction__project=task.project)
        task.teams.remove(team)
    except Team.DoesNotExist:
        pass
    return render(request, 'common/partials/_selected_teams.html', {'task': task})
