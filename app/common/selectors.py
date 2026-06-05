from .constants import FILTER_HEADERS


def get_page_filters(request) -> dict:
    """Extract filter values from the request's GET parameters.
    """
    return {
        key: request.GET.get(key, "")
        for key in FILTER_HEADERS
    }
