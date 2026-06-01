from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from project_tasks.views import check_project_access, get_project_or_404
from project_tasks.models import Task
from projects.models import ProjectMembership
from core.models import Notification

from .models import RequestComment, TaskRequest


def can_handle_requests(user, project):
    if not user.is_authenticated:
        return False
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership and membership.role in ('tech_support', 'manager', 'admin', 'owner')


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
            RequestComment.objects.create(request=req, author=request.user, text=text)
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
