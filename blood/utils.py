from django.core.mail import send_mail
from django.conf import settings

def send_status_email(user_email, subject, message):
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER, # From email
            [user_email],             # To email
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email failed to send: {e}")