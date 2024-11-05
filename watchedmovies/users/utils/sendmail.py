from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from config.settings.base import env


def send_email(*, to: str, template: str = "", subject: str = "", context: dict = {}) -> None:
    host_email = env("EMAIL_HOST_USER")
    subject = subject or "WatchedMovies"
    html_message = render_to_string(template, context or {})
    plain_message = strip_tags(html_message)
    from_email = host_email

    send_mail(subject, plain_message, from_email, [to], html_message=html_message)
