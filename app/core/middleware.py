from django.contrib.messages import get_messages
from django.template.loader import render_to_string

class HtmxMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.headers.get('HX-Request') and response.get('Content-Type', '').startswith('text/html'):
            storage = get_messages(request)
            messages_list = list(storage)
            if messages_list:
                messages_html = render_to_string('partials/_messages.html', {'messages': messages_list})
                content = response.content.decode('utf-8')
                response.content = messages_html + content

        return response