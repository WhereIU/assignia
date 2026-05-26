from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from projects.models import Project


def home(request):
    if request.user.is_authenticated:
        return redirect('projects:dashboard')

    public_projects = Project.objects.filter(is_public=True).order_by('?')[:6]
    return render(request, 'core/home.html', {'public_projects': public_projects})


@login_required
def notifications_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})


def about(request):
    return render(request, 'core/about.html')


def tutorials(request):
    return render(request, 'core/tutorials.html')