from django.shortcuts import render
from projects.models import Project

def home(request):
    public_projects = Project.objects.filter(is_public=True).order_by('-created_at')[:5]
    return render(request, 'core/home.html', {'public_projects': public_projects})
