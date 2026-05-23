from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse

from projects.models import Project, ProjectMembership
from users.models import User

from .models import RequestMessage, Task, TaskRequest, Comment
from .forms import TaskCreateForm


def get_project_or_404(username, slug):
    """Gets a project by owner and slug, otherwise returns 404."""
    return get_object_or_404(Project, owner__username=username, slug=slug)


def check_project_access(user, project):
    """Checks whether the user has access to the project."""
    if project.is_public:
        return True
    if user.is_authenticated:
        return ProjectMembership.objects.filter(user=user, project=project).exists()
    return False


def is_privileged(user, project):
    """Checks whether the user privileged as manager, admin, or owner of the project."""
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
def create_task(request, username, slug):
    project = get_project_or_404(username, slug)
    if not ProjectMembership.objects.filter(user=request.user, project=project).exists():
        return HttpResponseForbidden("Вы не участник проекта")

    if request.method == 'POST':
        form = TaskCreateForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.creator = request.user
            task.save()
            messages.success(request, f'Задача «{task.title}» создана!')
            return redirect('projects:detail_project', username=username, slug=slug)
    else:
        form = TaskCreateForm(project=project)

    return render(request, 'tasks/task_create.html', {
        'form': form,
        'project': project,
    })


def detail_task(request, task_pk):
    """The full task page.
    Available to everyone for public projects, otherwise only to participants."""
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
        context['project_members'] = ProjectMembership.objects.filter(
            project=project
        ).select_related('user')

    return render(request, 'tasks/task_detail.html', context)


@login_required
def edit_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    project_members = ProjectMembership.objects.filter(project=task.project).select_related('user')
    return render(request, 'tasks/partials/_task_edit.html', {
        'task': task,
        'project_members': project_members,
    })


@login_required
@require_http_methods(["POST"])
def save_task(request, task_pk):
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
    assignee_id = request.POST.get('assignee_id')
    if assignee_id:
        try:
            task.assignee = User.objects.get(pk=assignee_id)
        except User.DoesNotExist:
            pass
    else:
        task.assignee = None
    task.save()
    return render(request, 'tasks/partials/_task_view.html', {
        'task': task,
        'is_privileged': True,
        'project_members': ProjectMembership.objects.filter(project=task.project).select_related('user'),
    })


@login_required
def search_members(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    query = request.GET.get('assignee_search', '').strip()
    members = ProjectMembership.objects.filter(project=task.project).select_related('user')
    if query:
        members = members.filter(user__username__icontains=query)[:10]
    return render(request, 'common/partials/_member_list.html', {'members': members})


@login_required
@require_http_methods(["POST"])
def take_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not ProjectMembership.objects.filter(user=request.user, project=task.project).exists():
        return HttpResponseForbidden("Вы не участник проекта")
    if task.status != 'new' or task.assignee is not None:
        return HttpResponse("Задача уже занята или не новая", status=400)

    task.assignee = request.user
    task.status = 'in_progress'
    task.save()
    return render(request, 'tasks/partials/_task_item.html', {
        'task': task,
        'show_take_button': False,
    })


@login_required
@require_http_methods(["POST"])
def delete_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    membership = ProjectMembership.objects.filter(user=request.user, project=task.project).first()
    if not membership:
        return HttpResponseForbidden("Вы не участник проекта")
    if membership.role == 'participant':
        if task.creator != request.user:
            return HttpResponseForbidden("Вы не автор задачи")
        if task.status not in ('new', 'pending') or task.assignee is not None:
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
def restore_task(request, task_pk):
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
def change_status(request, task_pk):
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
def change_priority(request, task_pk):
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
def change_risk(request, task_pk):
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
def assign_user(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not is_privileged(request.user, task.project):
        return HttpResponseForbidden("Недостаточно прав")
    user_id = request.POST.get('user_id')
    if not user_id:
        task.assignee = None
    else:
        try:
            user = User.objects.get(pk=user_id)
            if not ProjectMembership.objects.filter(user=user, project=task.project).exists():
                return HttpResponse("Пользователь не участник проекта", status=400)
            task.assignee = user
        except User.DoesNotExist:
            return HttpResponse("Пользователь не найден", status=404)
    if task.assignee and task.status == 'new':
        task.status = 'in_progress'
    task.save()
    return render(request, 'tasks/partials/_task_item.html', {'task': task})


@login_required
@require_http_methods(["POST"])
def add_comment(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    text = request.POST.get('text', '').strip()
    if text:
        Comment.objects.create(task=task, author=request.user, text=text)
    comments = task.comments.order_by('-created_at')
    return render(request, 'common/partials/_comments.html', {
        'task': task,
        'comments': comments,
    })


@login_required
@require_http_methods(["POST"])
def create_request(request, username, slug):
    project = get_project_or_404(username, slug)
    if not check_project_access(request.user, project):
        return HttpResponseForbidden("Вы не можете оставлять запросы в этом проекте")

    description = request.POST.get('description', '').strip()
    if description:
        TaskRequest.objects.create(project=project, author=request.user, description=description)
        return HttpResponse("<div class='alert alert-success'>Запрос отправлен</div>")
    return HttpResponse("<div class='alert alert-danger'>Введите описание</div>", status=400)


@login_required
def project_requests_tab(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")

    if can_handle_requests(request.user, project):
        requests_qs = TaskRequest.objects.filter(project=project).order_by('-created_at')
    else:
        requests_qs = TaskRequest.objects.filter(project=project, author=request.user).order_by('-created_at')

    context = {
        'project': project,
        'requests': requests_qs,
        'is_tech_support': can_handle_requests(request.user, project),
    }
    if request.headers.get('HX-Request'):
        return render(request, 'requests/partials/_requests.html', context)
    return render(request, 'projects/project_detail.html', {**context, 'tab': 'requests'})


@login_required
def detail_request(request, username, slug, request_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    req = get_object_or_404(TaskRequest, pk=request_pk, project=project)
    if req.author != request.user and not can_handle_requests(request.user, project):
        return HttpResponseForbidden("Нет доступа к этому запросу")
    messages_list = req.messages.order_by('created_at')
    return render(request, 'requests/request_detail.html', {
        'project': project,
        'req': req,
        'messages_list': messages_list,
        'is_tech_support': can_handle_requests(request.user, project),
    })


@login_required
def request_add_message(request, username, slug, request_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    req = get_object_or_404(TaskRequest, pk=request_pk, project=project)
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
def request_convert_to_task(request, username, slug, request_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    req = get_object_or_404(TaskRequest, pk=request_pk, project=project)
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
    return redirect('tasks:detail_task', task_pk=task.pk)


@login_required
@require_http_methods(["POST"])
def delete_request(request, username, slug, request_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    req = get_object_or_404(TaskRequest, pk=request_pk, project=project)
    if req.author != request.user:
        return HttpResponseForbidden("Вы не автор запроса")
    if req.status != 'pending':
        return HttpResponse("Запрос уже обработан, нельзя удалить", status=400)
    req.delete()
    messages.success(request, 'Запрос удалён')

    redirect_url = reverse('tasks:project_requests_tab', kwargs={
        'username': username,
        'slug': slug,
    })
    response = HttpResponse(status=204)
    response['HX-Redirect'] = redirect_url
    return response



@login_required
def request_create_form(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")
    return render(request, 'requests/partials/_request_create_form.html', {'project': project})


@login_required
@require_http_methods(["POST"])
def request_create_submit(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")
    description = request.POST.get('description', '').strip()
    if description:
        TaskRequest.objects.create(project=project, author=request.user, description=description)
        messages.success(request, 'Запрос создан')
    if can_handle_requests(request.user, project):
        requests_qs = TaskRequest.objects.filter(project=project).order_by('-created_at')
    else:
        requests_qs = TaskRequest.objects.filter(project=project, author=request.user).order_by('-created_at')
    context = {
        'project': project,
        'requests': requests_qs,
        'is_tech_support': can_handle_requests(request.user, project),
    }
    return render(request, 'requests/partials/_requests.html', context)
