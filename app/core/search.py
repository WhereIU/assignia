import re
from django.db.models import Q

def parse_search_query(query: str):
    """Parses a search query with qualifiers."""
    filters = {
        'owner': None,
        'project': None,
        'status': None,
        'priority': None,
        'priority_op': None,
        'is_public': None,
        'search_fields': ['name', 'description'],
        'free_text': '',
    }

    qualifiers = [
        (r'\bpriority:(>=?|<=?|>|<|=)?(\d+)', 'priority'),
        (r'\bstatus:(new|pending|in_progress|done|cancelled)\b', 'status'),
        (r'\bis:(public|private|open|done)\b', 'is_public'),
        (r'\bin:(name|description|all)\b', 'in'),
        (r'\bowner:(\w+)', 'owner'),
        (r'\bproject:([\w-]+)', 'project'),
    ]

    remaining = query

    for pattern, key in qualifiers:
        match = re.search(pattern, remaining, re.IGNORECASE)
        if match:
            if key == 'priority':
                op = match.group(1) or ''
                value = int(match.group(2))
                filters['priority'] = value
                filters['priority_op'] = op
            elif key == 'status':
                filters['status'] = match.group(1).lower()
            elif key == 'is_public':
                val = match.group(1).lower()
                if val in ('public', 'private'):
                    filters['is_public'] = (val == 'public')
                elif val == 'open':
                    filters['status'] = 'new'
                elif val == 'done':
                    filters['status'] = 'done'
            elif key == 'in':
                fields = match.group(1).lower()
                if fields == 'all':
                    filters['search_fields'] = ['name', 'description']
                elif fields == 'name':
                    filters['search_fields'] = ['name']
                elif fields == 'description':
                    filters['search_fields'] = ['description']
            elif key in ('owner', 'project'):
                filters[key] = match.group(1)
            remaining = re.sub(pattern, '', remaining, count=1).strip()

    filters['free_text'] = remaining.strip()
    return filters


def apply_project_search_filters(queryset, filters):
    """Applies filters to projects."""
    q = Q()

    free = filters.get('free_text', '')
    if free:
        text_q = Q()
        if 'name' in filters.get('search_fields', []):
            text_q |= Q(name__icontains=free)
        if 'description' in filters.get('search_fields', []):
            text_q |= Q(description__icontains=free)
        if text_q:
            q &= text_q

    if filters.get('owner'):
        q &= Q(owner__username=filters['owner'])
    if filters.get('project'):
        q &= Q(slug__icontains=filters['project'])
    if filters.get('is_public') is not None:
        q &= Q(is_public=filters['is_public'])

    return queryset.filter(q) if q else queryset


def apply_task_search_filters(queryset, filters):
    """Applies filters to tasks."""
    q = Q()

    free = filters.get('free_text', '')
    if free:
        text_q = Q()
        if 'name' in filters.get('search_fields', []):
            text_q |= Q(title__icontains=free)
        if 'description' in filters.get('search_fields', []):
            text_q |= Q(description__icontains=free)
        if text_q:
            q &= text_q

    if filters.get('status'):
        q &= Q(status=filters['status'])
    if filters.get('priority') is not None:
        op = filters.get('priority_op', '')
        value = filters['priority']
        if op == '' or op == '=':
            q &= Q(priority=value)
        elif op == '>':
            q &= Q(priority__gt=value)
        elif op == '>=':
            q &= Q(priority__gte=value)
        elif op == '<':
            q &= Q(priority__lt=value)
        elif op == '<=':
            q &= Q(priority__lte=value)

    if filters.get('owner'):
        q &= Q(project__owner__username=filters['owner'])
    if filters.get('project'):
        q &= Q(project__slug__icontains=filters['project'])

    return queryset.filter(q) if q else queryset
