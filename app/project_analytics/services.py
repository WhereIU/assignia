from __future__ import annotations
from typing import Any, Dict, TYPE_CHECKING

from .selectors import get_participants_analytics, get_teams_analytics

if TYPE_CHECKING:
    from projects.models import Project


def get_analytics_data(project: Project) -> Dict[str, Any]:
    """Collect and return analytics context for project."""
    return {
        'project': project,
        'teams': get_teams_analytics(project),
        'participants': get_participants_analytics(project),
    }