import uuid

from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def generate_email_confirmation_token(user, new_email):
    token = str(uuid.uuid4())
    cache_key = f'email_confirmation:{token}'
    cache.set(cache_key, {'user_id': user.pk, 'new_email': new_email}, timeout=3600)
    return token


def send_email_confirmation(user, new_email):
    token = generate_email_confirmation_token(user, new_email)
    confirmation_url = settings.BASE_URL + reverse('users:confirm_email', kwargs={'token': token})
    subject = 'Подтверждение email в Assignia'
    message = f'Здравствуйте, {user.username}!\n\nПерейдите по ссылке для подтверждения email: {confirmation_url}'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_email])
