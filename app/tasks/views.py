from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from projects.models import Project, ProjectMembership
from .models import Task, TaskRequest, Comment, Notification

@login_required
@require_http_methods(["POST"])
def take_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    membership = ProjectMembership.objects.filter(user=request.user, project=task.project).first()
    if not membership:
        return HttpResponseForbidden("Вы не участник проекта")
    if task.status != 'new' or task.assignee is not None:
        return HttpResponse("Задача уже занята или не новая", status=400)
    task.assignee = request.user
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
    return render(request, 'tasks/partials/_comments.html', {'task': task, 'comments': comments})

@login_required
@require_http_methods(["POST"])
def create_request(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    description = request.POST.get('description', '').strip()
    if description:
        TaskRequest.objects.create(project=project, author=request.user, description=description)
        return HttpResponse("<div class='alert alert-success'>Запрос отправлен</div>")
    return HttpResponse("<div class='alert alert-danger'>Введите описание</div>", status=400)

def task_detail(request, username, slug, task_pk):
    """Полная страница задачи."""
    task = get_object_or_404(Task, pk=task_pk, project__owner__username=username, project__slug=slug)
    project = task.project
    comments = task.comments.order_by('-created_at')
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'project': project,
        'comments': comments,
    })

@login_required
def notifications_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'tasks/notifications.html', {'notifications': notifications})