from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum, F
from django.http import HttpResponseForbidden

from project_tasks.views import Project, ProjectMembership
from project_teams.models import Team
from users.models import User


@login_required
def analytics_tab(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not ProjectMembership.objects.filter(user=request.user, project=project).exists():
        return HttpResponseForbidden("Вы не участник проекта")

    task_filter = Q(tasks__project=project) & ~Q(tasks__status='cancelled')

    teams = Team.objects.filter(direction__project=project).annotate(
        total_tasks=Count('tasks', filter=task_filter),
        new_tasks=Count('tasks', filter=task_filter & Q(tasks__status='new')),
        pending_tasks=Count('tasks', filter=task_filter & Q(tasks__status='pending')),
        in_progress_tasks=Count('tasks', filter=task_filter & Q(tasks__status='in_progress')),
        done_tasks=Count('tasks', filter=task_filter & Q(tasks__status='done')),
        avg_priority=Avg('tasks__priority', filter=task_filter),
        total_risk=Sum(F('tasks__risk_chance') * F('tasks__risk_impact'), filter=task_filter),
    )

    assign_filter = Q(task_assignments__task__project=project) & ~Q(task_assignments__task__status='cancelled')

    participants = User.objects.filter(
        projectmembership__project=project
    ).annotate(
        assigned_count=Count('task_assignments', filter=assign_filter),
        done_count=Count('task_assignments', filter=assign_filter & Q(task_assignments__task__status='done')),
        performance_score=Sum(
            (F('task_assignments__task__priority') * (1 + F('task_assignments__task__risk_chance') * F('task_assignments__task__risk_impact') / 10.0)),
            filter=Q(task_assignments__task__project=project, task_assignments__task__status='done')
        ),
    )

    context = {'project': project, 'teams': teams, 'participants': participants}
    if request.headers.get('HX-Request'):
        return render(request, 'project_analytics/partials/_analytics_tab.html', context)
    return render(request, 'projects/project_detail.html', {**context, 'tab': 'analytics'})
