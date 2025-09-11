import smtplib, ssl
from email.message import EmailMessage
from app.core.config import settings

def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email

    if settings.EMAIL_BACKEND == "smtp":
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls(context=context)  # Upgrade connection to secure TLS
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)