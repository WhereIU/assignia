from __future__ import annotations
from typing import Any, Dict, TYPE_CHECKING

from project_members.constants import ProjectRole
from common.selectors import get_paginated_page

from .selectors import get_participants_analytics, get_teams_analytics


if TYPE_CHECKING:
    from projects.models import Project
    from django.http import QueryDict


def get_analytics_widget_context(
    project: Project, 
    widget_type: str, 
    block_id: str, 
    query_params: QueryDict
) -> Dict[str, Any]:
    """Build paginated context for analytics widget."""
    search_query = query_params.get('q', '').strip()
    page_number = query_params.get('page', 1)

    context = {
        'project': project,
        'widget_type': widget_type,
        'block_id': block_id,
        'search_query': search_query,
    }

    if widget_type == 'teams':
        teams_data = get_teams_analytics(project, search_query=search_query)
        context['page_obj'] = get_paginated_page(teams_data, page_number, per_page=3)

    elif widget_type == 'participants':
        role_filter = query_params.get('role', '')
        parts_data = get_participants_analytics(
            project, 
            search_query=search_query, 
            role_filter=role_filter
        )
        context['page_obj'] = get_paginated_page(parts_data, page_number, per_page=4)
        context['role_filter'] = role_filter
        context['project_roles'] = ProjectRole

    return context
