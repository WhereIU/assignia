from typing import Dict, Any
from projects.models import Project

from .selectors import get_teams_analytics, get_participants_analytics


def get_analytics_data(project: Project) -> Dict[str, Any]:
    """Collect and return analytics context for project."""
    return {
        'project': project,
        'teams': get_teams_analytics(project),
        'participants': get_participants_analytics(project),
    }
