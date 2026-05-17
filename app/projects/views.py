from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from .models import Project, ProjectMembership
from users.models import User
from tasks.models import Task
from django.db.models import Count, Q


def public_projects(request):
    projects = Project.objects.filter(is_public=True).order_by('-created_at')
    return render(request, 'projects/public_projects.html', {'projects': projects})

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_public:
        if not request.user.is_authenticated:
            return redirect('users:login')
        membership = ProjectMembership.objects.filter(user=request.user, project=project).first()
        if not membership:
            return redirect('core:home')
    tasks = Task.objects.filter(project=project, is_deleted=False).order_by('-priority')
    return render(request, 'projects/project_detail.html', {'project': project, 'tasks': tasks})

@login_required
def dashboard(request):
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

@login_required
def analytics(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)

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

    return render(request, 'projects/analytics.html', {
        'project': project,
        'directions': directions,
        'participants': participants,
    })