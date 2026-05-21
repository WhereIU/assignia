from django.shortcuts import render, redirect
from projects.models import Project

def home(request):
    if request.user.is_authenticated:
        return redirect('projects:dashboard')
    
    public_projects = Project.objects.filter(is_public=True).order_by('?')[:6]
    return render(request, 'core/home.html', {'public_projects': public_projects})