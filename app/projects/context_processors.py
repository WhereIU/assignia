from .models import ProjectMembership

def membership_roles(request):
    return {
        'membership_roles': ProjectMembership.ROLE_CHOICES,
    }