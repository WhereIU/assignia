from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from common.selectors import get_page_filters
from project_members.selectors import get_memberships_for_user
from projects.selectors import (
    get_pending_invitations_for_user,
    get_recent_public_projects,
)
from project_tasks.selectors import get_available_tasks_for_projects, get_tasks_assigned_to_user
from project_tasks.services import apply_tasks_filters


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    public_projects = get_recent_public_projects(limit=6)
    return render(request, "core/home.html", {"public_projects": public_projects})


@login_required
def notifications_list(request: HttpRequest) -> HttpResponse:
    notifications = request.user.notifications.order_by("-created_at")
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "core/notifications.html", {"notifications": notifications})


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    memberships = get_memberships_for_user(request.user)
    user_projects = [m.project for m in memberships]
    project_ids = [p.id for p in user_projects]

    source = request.GET.get("source", "assigned")
    if source == "assigned":
        tasks = get_tasks_assigned_to_user(request.user)
    else:
        tasks = get_available_tasks_for_projects(project_ids)

    filters = get_page_filters(request)
    tasks = apply_tasks_filters(tasks, filters)

    page = request.GET.get("page", 1)
    if request.headers.get("HX-Target") == "task-list-inner":
        paginator = Paginator(tasks, 10)
        page_obj = paginator.get_page(page)
        return render(
            request,
            "core/partials/_dashboard_tab.html",
            {
                "page_obj": page_obj,
                "show_take_button": source != "assigned",
                "filters": filters,
                "source": source,
            },
        )

    invitations = get_pending_invitations_for_user(request.user)
    return render(
        request,
        "core/dashboard.html",
        {
            "user_projects": user_projects,
            "filters": filters,
            "invitations": invitations,
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "core/about.html")


def tutorials(request: HttpRequest) -> HttpResponse:
    return render(request, "core/tutorials.html")
