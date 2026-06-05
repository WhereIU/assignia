from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from project_members.permissions import is_project_member
from projects.selectors import get_project

from .services import get_analytics_data


@login_required
def analytics_tab(request: HttpRequest, username: str, slug: str) -> HttpResponse:
    project = get_project(username=username, slug=slug)

    if not is_project_member(request.user, project):
        return HttpResponseForbidden("Вы не участник проекта")

    context = get_analytics_data(project)

    template = (
        'analytics/partials/_analytics_tab.html'
        if request.headers.get('HX-Request')
        else 'projects/project_detail.html'
    )
    if not request.headers.get('HX-Request'):
        context['tab'] = 'analytics'

    return render(request, template, context)
