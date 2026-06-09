from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from project_members.permissions import is_project_member
from projects.selectors import get_project

from .services import get_analytics_widget_context


@login_required
def analytics_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return analytics tab."""
    project = get_project(username=username, slug=slug)
    if not project:
        raise Http404("Проект не найден")

    if not is_project_member(request.user, project):
        return HttpResponseForbidden("Вы не участник проекта")

    context = {'project': project}

    if request.headers.get('HX-Request'):
        return render(request, 'analytics/partials/_analytics_tab.html', context)

    context['active_tab'] = 'analytics'
    return render(request, 'projects/project_detail.html', context)


@login_required
def analytics_widget_element(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    """Return analytic tab."""
    project = get_project(username=username, slug=slug)
    if not project or not is_project_member(request.user, project):
        return HttpResponseForbidden()

    widget_type = request.GET.get('type')
    block_id = request.GET.get('block_id', '1')
    
    context = get_analytics_widget_context(project, widget_type, block_id, request.GET)
    template = f'analytics/partials/_{widget_type}_widget_content.html'
    
    return render(request, template, context)
