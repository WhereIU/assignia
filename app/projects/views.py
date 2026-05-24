from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.urls import reverse


from tasks.models import Task
from users.models import User
from core.models import Notification

from .forms import ProjectCreateForm
from .models import Direction, Project, ProjectMembership, Invitation


def get_member_role(user, project):
    if not user.is_authenticated:
        return None
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership.role if membership else None


def can_manage_member(actor, target_membership, project):
    if not actor.is_authenticated:
        return False
    actor_role = get_member_role(actor, project)
    if not actor_role:
        return False
    if actor_role == 'owner':
        return True
    if actor_role == 'admin':
        return target_membership.role in ('manager', 'tech_support', 'participant')
    return False


def redirect_to_members(request, project):
    members = ProjectMembership.objects.filter(project=project).select_related('user')
    member_list = []
    for m in members:
        m.can_manage = can_manage_member(request.user, m, project)
        member_list.append(m)
    actor_role = get_member_role(request.user, project)
    pending_invitations = Invitation.objects.filter(project=project, status='pending').select_related('recipient')
    return render(request, 'projects/partials/_members.html', {
        'project': project,
        'members': member_list,
        'actor_role': actor_role,
        'pending_invitations': pending_invitations,
    })


def can_change_role_to(actor, target_membership, new_role, project):
    if not can_manage_member(actor, target_membership, project):
        return False
    actor_role = get_member_role(actor, project)
    if actor_role == 'owner':
        return True
    if actor_role == 'admin':
        allowed_roles = ['manager', 'tech_support', 'participant']
        return new_role in allowed_roles
    return False


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
    invitations = Invitation.objects.filter(recipient=request.user, status='pending')
    context = {
        'tasks': tasks,
        'show_take_button': show_take_button,
        'filters': filters,
        'source': source,
        'target_id': 'dashboard-content',
        'invitations': invitations,

    }

    if request.headers.get('HX-Request'):
        return render(request, 'projects/partials/_dashboard_tabs.html', context)

    return render(request, 'projects/dashboard.html', {
        **context,
        'user_projects': user_projects,
        'assigned_tasks': assigned_tasks,
        'available_tasks': available_tasks,
    })


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST, initial={'owner': request.user})
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            ProjectMembership.objects.create(user=request.user, project=project, role='owner')
            messages.success(request, f'Проект «{project.name}» создан!')
            return redirect('projects:detail_project', username=request.user.username, slug=project.slug)
    else:
        form = ProjectCreateForm(initial={'owner': request.user})
    return render(request, 'projects/project_create.html', {'form': form})


def detail_project(request, username, slug):
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
def join_project(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not project.is_public:
        return HttpResponseForbidden("Нельзя вступить в приватный проект.")
    if ProjectMembership.objects.filter(user=request.user, project=project).exists():
        messages.info(request, 'Вы уже участник этого проекта.')
    else:
        ProjectMembership.objects.create(user=request.user, project=project, role='participant')
        messages.success(request, f'Вы вступили в проект «{project.name}»!')
    return redirect('projects:detail_project', username=username, slug=slug)


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
def project_analytics_tab(request, username, slug):
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
def project_members(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    return redirect_to_members(request, project)


@login_required
def send_invitation(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    recipient_username = request.POST.get('username', '').strip()
    try:
        recipient = User.objects.get(username=recipient_username)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден')
        return redirect_to_members(request, project)
    if ProjectMembership.objects.filter(user=recipient, project=project).exists():
        messages.error(request, f'{recipient.username} уже участник')
        return redirect_to_members(request, project)
    if Invitation.objects.filter(project=project, recipient=recipient, status='pending').exists():
        messages.error(request, 'Приглашение уже отправлено')
        return redirect_to_members(request, project)
    Invitation.objects.create(project=project, sender=request.user, recipient=recipient)
    messages.success(request, f'Приглашение отправлено {recipient.username}')
    return redirect_to_members(request, project)


@login_required
def cancel_invitation(request, username, slug, invitation_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    invitation = get_object_or_404(Invitation, pk=invitation_pk, project=project, status='pending')
    invitation.status = 'cancelled'
    invitation.save()
    notification_url = reverse('projects:accept_invitation', kwargs={'invitation_pk': invitation.pk})
    Notification.objects.filter(recipient=invitation.recipient, url=notification_url).delete()
    messages.success(request, f'Приглашение {invitation.recipient.username} отменено')
    return redirect_to_members(request, project)


@login_required
def accept_invitation(request, invitation_pk):
    invitation = get_object_or_404(Invitation, pk=invitation_pk, recipient=request.user, status='pending')
    project = invitation.project
    if ProjectMembership.objects.filter(user=request.user, project=project).exists():
        invitation.status = 'accepted'
        invitation.save()
        messages.info(request, 'Вы уже участник проекта')
    else:
        ProjectMembership.objects.create(user=request.user, project=project, role='participant')
        invitation.status = 'accepted'
        invitation.save()
        messages.success(request, f'Вы вступили в проект «{project.name}»')
    return redirect('projects:detail_project', username=project.owner.username, slug=project.slug)


@login_required
def decline_invitation(request, invitation_pk):
    invitation = get_object_or_404(Invitation, pk=invitation_pk, recipient=request.user, status='pending')
    notification_url = reverse('projects:accept_invitation', kwargs={'invitation_pk': invitation.pk})
    Notification.objects.filter(recipient=request.user, url=notification_url).delete()
    invitation.status = 'declined'
    invitation.save()
    messages.info(request, 'Приглашение отклонено')
    return redirect('core:home')


@login_required
@require_http_methods(["POST"])
def change_member_role(request, username, slug, user_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    target_membership = get_object_or_404(ProjectMembership, user__pk=user_pk, project=project)
    if target_membership.role == 'owner':
        messages.error(request, 'Нельзя изменить роль владельца')
        return redirect_to_members(request, project)

    new_role = request.POST.get('role')
    if new_role not in dict(ProjectMembership.ROLE_CHOICES):
        messages.error(request, 'Неверная роль')
        return redirect_to_members(request, project)
    if new_role == 'owner':
        messages.error(request, 'Нельзя назначить владельца через смену роли. Используйте передачу владения.')
        return redirect_to_members(request, project)
    if actor_role == 'admin' and target_membership.role == 'admin':
        messages.error(request, 'Недостаточно прав')
        return redirect_to_members(request, project)
    target_membership.role = new_role
    target_membership.save()
    messages.success(request, f'Роль {target_membership.user.username} изменена на {new_role}')
    return redirect_to_members(request, project)


@login_required
@require_http_methods(["POST"])
def remove_member(request, username, slug, user_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    target_membership = get_object_or_404(ProjectMembership, user__pk=user_pk, project=project)
    if target_membership.role == 'owner':
        messages.error(request, 'Нельзя удалить владельца')
        return redirect_to_members(request, project)
    if actor_role == 'admin' and target_membership.role == 'admin':
        messages.error(request, 'Недостаточно прав')
        return redirect_to_members(request, project)
    removed_username = target_membership.user.username
    target_membership.delete()
    messages.success(request, f'{removed_username} удалён из проекта')
    return redirect_to_members(request, project)