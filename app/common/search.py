import re
from typing import Any, Callable, Dict, List, Tuple

from django.db.models import Q, QuerySet
from project_tasks.constants import TaskStatus

from .constants import PROJECT_FIELD_MAP, TASK_FIELD_MAP


STATUS_VALUES = "|".join(TaskStatus.values)


def _handle_priority(match: re.Match, filters: Dict[str, Any]) -> None:
    op = match.group(1) or ""
    value = int(match.group(2))
    filters["priority"] = value
    filters["priority_op"] = op


def _handle_status(match: re.Match, filters: Dict[str, Any]) -> None:
    filters["status"] = match.group(1).lower()


def _handle_is(match: re.Match, filters: Dict[str, Any]) -> None:
    val = match.group(1).lower()
    if val in ("public", "private"):
        filters["is_public"] = (val == "public")
    elif val == "open":
        filters["status"] = "new"
    elif val == "done":
        filters["status"] = "done"


def _handle_in(match: re.Match, filters: Dict[str, Any]) -> None:
    fields = match.group(1).lower()
    if fields == "all":
        filters["search_fields"] = ["name", "description"]
    elif fields == "name":
        filters["search_fields"] = ["name"]
    elif fields == "description":
        filters["search_fields"] = ["description"]


def _handle_owner(match: re.Match, filters: Dict[str, Any]) -> None:
    filters["owner"] = match.group(1)


def _handle_project(match: re.Match, filters: Dict[str, Any]) -> None:
    filters["project"] = match.group(1)


QUALIFIERS: List[Tuple[str, Callable[[re.Match, Dict[str, Any]], None]]] = [
    (rf"priority:(>=?|<=?|>|<|=)?(\d+)", _handle_priority),
    (rf"status:({STATUS_VALUES})\b", _handle_status),
    (r"is:(public|private|open|done)\b", _handle_is),
    (r"in:(name|description|all)\b", _handle_in),
    (r"owner:(\w+)", _handle_owner),
    (r"project:([\w-]+)", _handle_project),
]


def parse_search_query(query: str) -> Dict[str, Any]:
    """Parse search query string into dictionary of filters."""
    filters: Dict[str, Any] = {
        "owner": None,
        "project": None,
        "status": None,
        "priority": None,
        "priority_op": None,
        "is_public": None,
        "search_fields": ["name", "description"],
        "free_text": "",
    }

    remaining = query
    for pattern, handler in QUALIFIERS:
        match = re.search(pattern, remaining, re.IGNORECASE)
        if match:
            handler(match, filters)
            remaining = re.sub(pattern, "", remaining, count=1).strip()

    filters["free_text"] = remaining.strip()
    return filters


def _build_text_search_q(
    free_text: str, search_fields: List[str], field_map: Dict[str, str]
) -> Q:
    """Build Q object for search across fields."""
    if not free_text:
        return Q()
    q = Q()
    for field in search_fields:
        if field in field_map:
            q |= Q(**{f"{field_map[field]}__icontains": free_text})
    return q




def apply_project_search_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
    """Apply parsed filters to project queryset."""
    q = Q()

    free = filters.get("free_text", "")
    if free:
        q &= _build_text_search_q(free, filters.get("search_fields", []), PROJECT_FIELD_MAP)

    if filters.get("owner"):
        q &= Q(owner__username=filters["owner"])
    if filters.get("project"):
        q &= Q(slug__icontains=filters["project"])
    if filters.get("is_public") is not None:
        q &= Q(is_public=filters["is_public"])

    return queryset.filter(q) if q else queryset


def apply_task_search_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
    """Apply parsed filters to task queryset."""
    q = Q()

    free = filters.get("free_text", "")
    if free:
        q &= _build_text_search_q(free, filters.get("search_fields", []), TASK_FIELD_MAP)

    if filters.get("status"):
        q &= Q(status=filters["status"])
    if filters.get("priority") is not None:
        op = filters.get("priority_op", "")
        value = filters["priority"]
        if op in ("", "="):
            q &= Q(priority=value)
        elif op == ">":
            q &= Q(priority__gt=value)
        elif op == ">=":
            q &= Q(priority__gte=value)
        elif op == "<":
            q &= Q(priority__lt=value)
        elif op == "<=":
            q &= Q(priority__lte=value)

    if filters.get("owner"):
        q &= Q(project__owner__username=filters["owner"])
    if filters.get("project"):
        q &= Q(project__slug__icontains=filters["project"])

    return queryset.filter(q) if q else queryset
