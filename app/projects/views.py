from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator

from core.models import Notification
from project_tasks.models import Task
from users.models import User

from .forms import ProjectCreateForm
from .models import Invitation, Project, ProjectMembership


def available_projects(request):
    query = request.GET.get('q', '').strip()
    projects = Project.objects.filter(is_public=True)

    if request.user.is_authenticated:
        private_ids = ProjectMembership.objects.filter(user=request.user).values('project')
        projects = projects | Project.objects.filter(pk__in=private_ids)
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
def project_create(request):
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST, initial={'owner': request.user})
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            ProjectMembership.objects.create(user=request.user, project=project, role='owner')
            messages.success(request, f'Проект «{project.name}» создан!')
            return redirect('projects:project_detail', username=request.user.username, slug=project.slug)
    else:
        form = ProjectCreateForm(initial={'owner': request.user})
    return render(request, 'projects/project_create.html', {'form': form})


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
    is_privileged = request.user.is_authenticated and get_member_role(request.user, project) in ('manager', 'admin', 'owner')
    filters = {'status': '', 'priority': '', 'risk': '', 'q': ''}
    if request.headers.get('HX-Request'):
        if any(request.GET.get(p) for p in ('status', 'priority', 'risk', 'q')):
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
            filters = {'status': status, 'priority': priority, 'risk': risk, 'q': q}
            return render(request, 'tasks/partials/_task_list.html', {
                'tasks': tasks,
                'show_take_button': True,
                'filters': filters,
            })

        return render(request, 'tasks/partials/_tasks_tab.html', {
            'tasks': tasks,
            'project': project,
            'is_member': is_member,
            'filters': filters,
        })

    return render(request, 'projects/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'is_member': is_member,
        'is_privileged': is_privileged,
        'filters': filters,
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


@login_required
def members_tab(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if get_member_role(request.user, project) not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")

    members = ProjectMembership.objects.filter(project=project).select_related('user')
    search_query = request.GET.get('search', '').strip()
    page = request.GET.get('page', 1)

    if search_query:
        members = members.filter(user__username__icontains=search_query)

    paginator = Paginator(members, 10)
    page_obj = paginator.get_page(page)

    actor_role = get_member_role(request.user, project)
    pending_invitations = Invitation.objects.filter(project=project, status='pending').select_related('recipient')

    if request.headers.get('HX-Target', '') == 'members-list-inner':
        return render(request, 'projects/partials/_members_list.html', {
            'project': project,
            'members': page_obj,
            'actor_role': actor_role,
            'page_obj': page_obj,
            'search_query': search_query,
        })

    return render(request, 'projects/partials/_members_tab.html', {
        'project': project,
        'members': page_obj,
        'actor_role': actor_role,
        'pending_invitations': pending_invitations,
        'page_obj': page_obj,
        'search_query': search_query,
    })


@login_required
def project_settings_tab(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if not can_manage_member(request.user, None, project):
        actor_role = get_member_role(request.user, project)
        if actor_role not in ('admin', 'owner'):
            return HttpResponseForbidden("Недостаточно прав")
    return render(request, 'projects/partials/_project_settings.html', {
        'project': project,
    })


@login_required
@require_http_methods(["POST"])
def invitation_send(request, username, slug):
    project = get_object_or_404(
        Project,
        owner__username=username,
        slug=slug,
    )

    if get_member_role(request.user, project) not in ("owner", "admin"):
        return HttpResponseForbidden("Недостаточно прав")

    recipient_username = request.POST.get("username", "").strip()

    if not recipient_username:
        messages.error(request, "Укажите имя пользователя")
        return redirect_to_members(request, project)

    try:
        recipient = User.objects.get(username=recipient_username)
    except User.DoesNotExist:
        messages.error(request, "Пользователь не найден")
        return redirect_to_members(request, project)

    if recipient == request.user:
        messages.error(request, "Нельзя пригласить самого себя")
        return redirect_to_members(request, project)

    if ProjectMembership.objects.filter(
        project=project,
        user=recipient,
    ).exists():
        messages.error(request, "Пользователь уже состоит в проекте")
        return redirect_to_members(request, project)

    if Invitation.objects.filter(
        project=project,
        recipient=recipient,
        status="pending",
    ).exists():
        messages.error(request, "Приглашение уже отправлено")
        return redirect_to_members(request, project)

    Invitation.objects.create(
        project=project,
        sender=request.user,
        recipient=recipient,
    )

    messages.success(
        request,
        f"Приглашение отправлено пользователю {recipient.username}",
    )

    return redirect_to_members(request, project)


@login_required
def invitation_cancel(request, username, slug, invitation_pk):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    if get_member_role(request.user, project) not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    invitation = get_object_or_404(Invitation, pk=invitation_pk, project=project, status='pending')
    invitation.status = 'cancelled'
    invitation.save()
    notification_url = reverse('projects:invitation_accept', kwargs={'invitation_pk': invitation.pk})
    Notification.objects.filter(recipient=invitation.recipient, url=notification_url).delete()
    messages.success(request, f'Приглашение {invitation.recipient.username} отменено')
    return redirect_to_members(request, project)


@login_required
def invitation_accept(request, invitation_pk):
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
    return redirect('projects:project_detail', username=project.owner.username, slug=project.slug)


@login_required
def invitation_decline(request, invitation_pk):
    invitation = get_object_or_404(Invitation, pk=invitation_pk, recipient=request.user, status='pending')
    notification_url = reverse('projects:invitation_accept', kwargs={'invitation_pk': invitation.pk})
    Notification.objects.filter(recipient=request.user, url=notification_url).delete()
    invitation.status = 'declined'
    invitation.save()
    messages.info(request, 'Приглашение отклонено')
    return redirect('core:home')


@login_required
@require_http_methods(["POST"])
def member_update_role(request, username, slug, user_pk):
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
        messages.error(request, 'Нельзя назначить владельца через смену роли.')
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
def member_remove(request, username, slug, user_pk):
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


@login_required
def project_settings_form(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    return render(request, 'projects/partials/_project_settings_form.html', {
        'project': project,
        'submit_url': reverse('projects:project_update', kwargs={'username': username, 'slug': slug}),
    })


@login_required
@require_http_methods(["POST"])
def project_update(request, username, slug):
    project = get_object_or_404(Project, owner__username=username, slug=slug)
    actor_role = get_member_role(request.user, project)
    if actor_role not in ('admin', 'owner'):
        return HttpResponseForbidden("Недостаточно прав")
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    is_public = request.POST.get('is_public') == 'on'
    if not name:
        messages.error(request, 'Название проекта не может быть пустым')
        return redirect('projects:project_settings_tab', username=username, slug=slug)
    project.name = name
    project.description = description
    if actor_role == 'owner':
        project.is_public = is_public
    project.save()
    messages.success(request, 'Настройки проекта обновлены')
    return redirect('projects:project_settings_tab', username=username, slug=slug)


def get_member_role(user, project):
    if not user.is_authenticated:
        return None
    membership = ProjectMembership.objects.filter(user=user, project=project).first()
    return membership.role if membership else None


def require_project_roles(user, project, *roles):
    return get_member_role(user, project) in roles


def can_manage_member(actor, target_membership, project):
    if not actor.is_authenticated:
        return False
    actor_role = get_member_role(actor, project)
    if not actor_role:
        return False
    if actor_role == 'owner':
        return True
    if actor_role == 'admin':
        return target_membership.role in ('manager', 'tech_support', 'hr_analyst', 'participant')
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
