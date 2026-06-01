from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, IntegerField

from project_tasks.models import Task
from projects.models import Invitation, Project, ProjectMembership


def home(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    public_projects = Project.objects.filter(is_public=True).order_by('?')[:6]
    return render(request, 'core/home.html', {'public_projects': public_projects})


@login_required
def notifications_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})


@login_required
def dashboard(request):
    memberships = ProjectMembership.objects.filter(user=request.user).select_related('project')
    user_projects = [m.project for m in memberships]

    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    risk_filter = request.GET.get('risk', '')
    q = request.GET.get('q', '')
    source = request.GET.get('source', 'assigned')
    page = request.GET.get('page', 1)

    if source == 'assigned':
        tasks = Task.objects.filter(assignments__user=request.user, is_deleted=False)
    else:
        tasks = Task.objects.filter(
            project__in=user_projects,
            status='new',
            assignments__isnull=True,
            is_deleted=False,
        )

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=int(priority_filter))
    if risk_filter == 'high':
        tasks = tasks.filter(Q(risk_chance__gte=4) | Q(risk_impact__gte=4))
    elif risk_filter == 'low':
        tasks = tasks.filter(risk_chance__lte=3, risk_impact__lte=3)
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))

    tasks = tasks.annotate(
        is_available=Case(
            When(assignments__isnull=True, then=1),
            default=0,
            output_field=IntegerField(),
        ),
        status_group=Case(
            When(status='new', then=1),
            When(status='pending', then=1),
            When(status='in_progress', then=1),
            When(status='done', then=2),
            When(status='cancelled', then=2),
            default=1,
            output_field=IntegerField(),
        )
        ).order_by(
            '-is_available',
            'status_group',
            '-priority',
            '-created_at'
        )

    filters = {
        'status': status_filter,
        'priority': str(priority_filter) if priority_filter else '',
        'risk': risk_filter,
        'q': q,
    }

    if request.headers.get('HX-Target', '') == 'task-list-inner':
        paginator = Paginator(tasks, 10)
        page_obj = paginator.get_page(page)
        return render(request, 'core/partials/_dashboard_tab.html', {
            'page_obj': page_obj,
            'show_take_button': source != 'assigned',
            'filters': filters,
            'source': source,
        })

    invitations = Invitation.objects.filter(recipient=request.user, status='pending')
    return render(request, 'core/dashboard.html', {
        'user_projects': user_projects,
        'filters': filters,
        'invitations': invitations,
    })


def about(request):
    return render(request, 'core/about.html')


def tutorials(request):
    return render(request, 'core/tutorials.html')
