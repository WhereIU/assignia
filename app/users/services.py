import uuid

from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

EMAIL_CONFIRMATION_TIMEOUT = 60 * 60


def _generate_email_confirmation_token(user, new_email=None):
    """Generate and store unique token for email confirmation."""
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
    """
    Send confirmation email.
    """
    token = _generate_email_confirmation_token(user, new_email)
    url = settings.BASE_URL + reverse("users:confirm_email", kwargs={"token": token})

    recipient = new_email or user.email
    try:
        send_mail(
            subject="Подтверждение email",
            message=f"Перейдите по ссылке:\n{url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as exc:
        raise RuntimeError("Не удалось отправить письмо.") from exc

    user.pending_email = new_email
    user.save(update_fields=["pending_email"])


def confirm_email_token(token):
    """Validate token and activate."""
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


def cancel_pending_email(user):
    """Cancel pending email change."""
    user.pending_email = None
    user.save(update_fields=["pending_email"])


def change_user_email(user, new_email):
    """
    Check for existing pending email,
    send confirmation and mark pending.
    """
    if user.pending_email:
        raise ValueError("У вас уже есть неподтверждённый email.")
    try:
        send_email_confirmation(user, new_email)
    except Exception as exc:
        raise RuntimeError("Не удалось отправить письмо.") from exc
    user.refresh_from_db()
