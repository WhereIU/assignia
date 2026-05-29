import uuid

from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


EMAIL_CONFIRMATION_TIMEOUT = 60 * 60


def generate_email_confirmation_token(user, new_email=None):
    old_token = cache.get(f"user_email_confirmation:{user.pk}")
    if old_token:
        cache.delete(f"email_confirmation:{old_token}")

    token = str(uuid.uuid4())
    cache.set(
        f"email_confirmation:{token}",
        {
            "user_id": user.id,
            "new_email": new_email,
        },
        timeout=EMAIL_CONFIRMATION_TIMEOUT,
    )

    return token


def send_email_confirmation(user, new_email=None):
    token = generate_email_confirmation_token(user, new_email)

    url = settings.BASE_URL + reverse("users:confirm_email", kwargs={"token": token})

    send_mail(
        subject="Подтверждение email",
        message=f"Перейдите по ссылке:\n{url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email or user.email],
        fail_silently=False,
    )

    user.pending_email = new_email
    user.save(update_fields=["pending_email"])

    return token


def confirm_email_token(token):
    data = cache.get(f"email_confirmation:{token}")
    if not data:
        return None

    from users.models import User
    
    user = User.objects.filter(id=data["user_id"]).first()
    if not user:
        return None

    if data["new_email"]:
        user.email = data["new_email"]
        user.pending_email = None
        user.save(update_fields=["email", "pending_email"])

    user.is_active = True
    user.save(update_fields=["is_active"])
    cache.delete(f"email_confirmation:{token}")

    return user
