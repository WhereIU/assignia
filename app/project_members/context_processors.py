from .constants import ProjectRole


def membership_roles(request):
    return {
        'membership_roles': ProjectRole.choices,
    }