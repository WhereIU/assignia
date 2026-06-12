from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from project_members.constants import ProjectRole
from projects.selectors import get_project
from common.selectors import get_paginated_page

from .selectors import get_participants_analytics, get_teams_analytics
from .permissions import ProjectAnalyticsPermissions


def analytics_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return project analytics tab."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectAnalyticsPermissions(request.user, project)
    if not perms.can_view_analytics:
        raise PermissionDenied("У вас нет прав для просмотра аналитики этого проекта")

    context = {'project': project}

    if request.headers.get('HX-Request'):
        return render(request, 'analytics/partials/_analytics_tab.html', context)

    context['active_tab'] = 'analytics'
    return render(request, 'projects/project_detail.html', context)


@require_http_methods(["GET"])
def analytics_widget_element(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return data block for specific analytics widget."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    perms = ProjectAnalyticsPermissions(request.user, project)
    if not perms.can_view_analytics:
        raise PermissionDenied()

    widget_type = request.GET.get('type')
    block_id = request.GET.get('block_id', '1')
    search_query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    context = {
        'project': project,
        'widget_type': widget_type,
        'block_id': block_id,
        'search_query': search_query,
    }

    if widget_type == 'teams':
        teams_data = get_teams_analytics(project, search_query=search_query)
        context['page_obj'] = get_paginated_page(teams_data, page_number, per_page=3)
        template = 'analytics/partials/_teams_widget_content.html'

    elif widget_type == 'participants':
        role_filter = request.GET.get('role', '')
        parts_data = get_participants_analytics(
            project, 
            search_query=search_query, 
            role_filter=role_filter
        )
        context['page_obj'] = get_paginated_page(parts_data, page_number, per_page=4)
        context['role_filter'] = role_filter
        context['project_roles'] = ProjectRole
        template = 'analytics/partials/_participants_widget_content.html'
        
    else:
        raise Http404("Неизвестный тип виджета")

    return render(request, template, context)
