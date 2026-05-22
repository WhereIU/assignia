from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from projects.models import Project, ProjectMembership

from .models import Task, TaskRequest, Comment
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


@login_required
@require_http_methods(["POST"])
def task_take(request, task_pk):
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
def task_create(request, username, slug):
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
            return redirect('projects:project_detail', username=username, slug=slug)
    else:
        form = TaskCreateForm(project=project)

    return render(request, 'tasks/task_create.html', {
        'form': form,
        'project': project,
    })


def task_detail(request, task_pk):
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
@require_http_methods(["POST"])
def add_comment(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    text = request.POST.get('text', '').strip()
    if text:
        Comment.objects.create(task=task, author=request.user, text=text)
    comments = task.comments.order_by('-created_at')
    return render(request, 'tasks/partials/_comments.html', {
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
