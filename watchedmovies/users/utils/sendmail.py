from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_emails(*, name: str, email: str) -> None:
    subject = "Welcome to Watched Movies!"
    html_message = render_to_string("success_mail.html", {"name": name})
    plain_message = strip_tags(html_message)
    from_email = "watchedmovies@noreply.com"
    to = email

    send_mail(subject, plain_message, from_email, [to], html_message=html_message)
