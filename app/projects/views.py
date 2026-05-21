from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Count, Q
from .models import Project, ProjectMembership, Direction
from tasks.models import Task, TaskRequest
from users.models import User
from .forms import ProjectCreateForm
from django.contrib import messages

def available_projects(request):
    query = request.GET.get('q', '').strip()
    
    projects = Project.objects.filter(is_public=True)
    
    if request.user.is_authenticated:
        private_memberships = ProjectMembership.objects.filter(user=request.user).values('project')
        projects = projects | Project.objects.filter(pk__in=private_memberships)
        projects = projects.distinct()
    
    if query:
        from core.search import parse_search_query, apply_project_search_filters
        filters = parse_search_query(query)
        projects = apply_project_search_filters(projects, filters)
    
    projects = projects.order_by('-created_at')
    return render(request, 'projects/available_projects.html', {
        'projects': projects,
        'query': query,
    })

@login_required
def dashboard(request):
    """Дашборд участника."""
    memberships = ProjectMembership.objects.filter(user=request.user).select_related('project')
    user_projects = [m.project for m in memberships]

    assigned_tasks = Task.objects.filter(assignee=request.user, is_deleted=False).order_by('-priority')
    available_tasks = Task.objects.filter(
        project__in=user_projects,
        status='new',
        assignee__isnull=True,
        is_deleted=False
    ).order_by('-priority')

    return render(request, 'projects/dashboard.html', {
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

    is_member = False
    if request.user.is_authenticated:
        is_member = ProjectMembership.objects.filter(user=request.user, project=project).exists()

    return render(request, 'projects/detail.html', {
        'project': project,
        'tasks': tasks,
        'tab': 'tasks',
        'is_member': is_member,
    })

@login_required
def project_tasks(request, username, slug):
    """HTMX partial: список задач."""
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    tasks = Task.objects.filter(project=project, is_deleted=False).order_by('-priority')
    return render(request, 'projects/partials/_tasks.html', {'project': project, 'tasks': tasks})

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

@login_required
def project_requests_content(request, username, slug):
    """HTMX или полная страница: мои запросы."""
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")

    user_requests = TaskRequest.objects.filter(project=project, author=request.user).order_by('-created_at')
    context = {'project': project, 'requests': user_requests}

    if request.headers.get('HX-Request'):
        return render(request, 'projects/partials/_requests.html', context)
    return render(request, 'projects/detail.html', {**context, 'tab': 'requests'})

@login_required
def project_analytics_content(request, username, slug):
    """HTMX или полная страница: аналитика."""
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
    return render(request, 'projects/detail.html', {**context, 'tab': 'analytics'})

@login_required
def project_request_create(request, username, slug):
    """Создание нового запроса."""
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return HttpResponseForbidden("Вы не участник проекта")

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        if description:
            TaskRequest.objects.create(project=project, author=request.user, description=description)
            return redirect('projects:project_requests_content', username=username, slug=slug)

    return render(request, 'projects/request_create.html', {'project': project})

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
    return render(request, 'projects/create.html', {'form': form})