from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from tasks.models import RequestMessage, Task, TaskRequest
from users.models import User

from .forms import ProjectCreateForm
from .models import Direction, Project, ProjectMembership


def available_projects(request):
    query = request.GET.get('q', '').strip()
    projects = Project.objects.filter(is_public=True)

    if request.user.is_authenticated:
        private_memberships = ProjectMembership.objects.filter(user=request.user).values('project')
        projects = projects | Project.objects.filter(pk__in=private_memberships)
        projects = projects.distinct()

    if query:
        from core.search import apply_project_search_filters, parse_search_query
        filters = parse_search_query(query)
        projects = apply_project_search_filters(projects, filters)

    projects = projects.order_by('-created_at')
    return render(request, 'projects/available_projects.html', {
        'projects': projects,
        'query': query,
    })


@login_required
def dashboard(request):
    memberships = ProjectMembership.objects.filter(user=request.user).select_related('project')
    user_projects = [m.project for m in memberships]

    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    risk_filter = request.GET.get('risk', '')
    q = request.GET.get('q', '')
    source = request.GET.get('source', 'assigned')

    assigned_tasks = Task.objects.filter(assignee=request.user, is_deleted=False)
    available_tasks = Task.objects.filter(
        project__in=user_projects,
        status='new',
        assignee__isnull=True,
        is_deleted=False,
    )

    if status_filter:
        assigned_tasks = assigned_tasks.filter(status=status_filter)
        available_tasks = available_tasks.filter(status=status_filter)
    if priority_filter:
        assigned_tasks = assigned_tasks.filter(priority=int(priority_filter))
        available_tasks = available_tasks.filter(priority=int(priority_filter))
    if risk_filter == 'high':
        assigned_tasks = assigned_tasks.filter(Q(risk_chance__gte=4) | Q(risk_impact__gte=4))
        available_tasks = available_tasks.filter(Q(risk_chance__gte=4) | Q(risk_impact__gte=4))
    elif risk_filter == 'low':
        assigned_tasks = assigned_tasks.filter(risk_chance__lte=3, risk_impact__lte=3)
        available_tasks = available_tasks.filter(risk_chance__lte=3, risk_impact__lte=3)
    if q:
        assigned_tasks = assigned_tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
        available_tasks = available_tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))

    assigned_tasks = assigned_tasks.order_by('-priority')
    available_tasks = available_tasks.order_by('-priority')

    filters = {
        'status': status_filter,
        'priority': str(priority_filter) if priority_filter else '',
        'risk': risk_filter,
        'q': q,
    }

    tasks = assigned_tasks if source == 'assigned' else available_tasks
    show_take_button = source != 'assigned'
    context = {
        'tasks': tasks,
        'show_take_button': show_take_button,
        'filters': filters,
        'source': source,
        'target_id': 'dashboard-content',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'projects/partials/_dashboard_tabs.html', context)

    return render(request, 'projects/dashboard.html', {
        **context,
        'user_projects': user_projects,
        'assigned_tasks': assigned_tasks,
        'available_tasks': available_tasks,
    })


def project_detail(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        if not request.user.is_authenticated:
            return redirect('users:login')
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")

    tasks = Task.objects.filter(project=project, is_deleted=False).order_by('-priority')
    is_member = request.user.is_authenticated and ProjectMembership.objects.filter(
        user=request.user, project=project
    ).exists()

    return render(request, 'projects/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'tab': 'tasks',
        'is_member': is_member,
    })


@login_required
def project_tasks(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
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
        'filters': {
            'status': status,
            'priority': str(priority) if priority else '',
            'risk': risk,
            'q': q,
        },
        'target_id': 'tab-content',
    })


@login_required
def project_join(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        return HttpResponseForbidden("Нельзя вступить в приватный проект.")
    if ProjectMembership.objects.filter(user=request.user, project=project).exists():
        messages.info(request, 'Вы уже участник этого проекта.')
    else:
        ProjectMembership.objects.create(user=request.user, project=project, role='participant')
        messages.success(request, f'Вы вступили в проект «{project.name}»!')
    return redirect('projects:project_detail', username=username, slug=slug)


def can_handle_requests(user, project):
    if not user.is_authenticated:
        return False
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership and membership.role in ('tech_support', 'manager', 'admin', 'owner')


@login_required
def project_requests_content(request, username, slug):
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
        return render(request, 'projects/partials/_requests.html', context)
    return render(request, 'projects/detail.html', {**context, 'tab': 'requests'})


@login_required
def request_detail(request, username, slug, request_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    req = get_object_or_404(TaskRequest, pk=request_pk, project=project)
    if req.author != request.user and not can_handle_requests(request.user, project):
        return HttpResponseForbidden("Нет доступа к этому запросу")
    messages_list = req.messages.order_by('created_at')
    return render(request, 'projects/request_detail.html', {
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
    return render(request, 'projects/partials/_request_messages.html', {
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
    return redirect('tasks:task_detail', task_pk=task.pk)


@login_required
def project_analytics_content(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
    if not membership:
        return HttpResponseForbidden("Вы не участник проекта")

    directions = project.directions.annotate(
        total_tasks=Count('tasks'),
        done_tasks=Count('tasks', filter=Q(tasks__status='done')),
        in_progress_tasks=Count('tasks', filter=Q(tasks__status='in_progress')),
        new_tasks=Count('tasks', filter=Q(tasks__status='new')),
    )

    participants = User.objects.filter(
        projectmembership__project=project
    ).annotate(
        assigned_count=Count('assigned_tasks', filter=Q(assigned_tasks__project=project)),
        done_count=Count('assigned_tasks', filter=Q(assigned_tasks__project=project, assigned_tasks__status='done')),
    )

    context = {
        'project': project,
        'directions': directions,
        'participants': participants,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'projects/partials/_analytics.html', context)
    return render(request, 'projects/project_detail.html', {**context, 'tab': 'analytics'})


@login_required
def request_create_form(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")
    return render(request, 'projects/partials/_request_create_form.html', {'project': project})


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
    return render(request, 'projects/partials/_requests.html', context)


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            ProjectMembership.objects.create(user=request.user, project=project, role='owner')
            messages.success(request, f'Проект «{project.name}» создан!')
            return redirect('projects:project_detail', username=request.user.username, slug=project.slug)
    else:
        form = ProjectCreateForm()
    return render(request, 'projects/project_create.html', {'form': form})
