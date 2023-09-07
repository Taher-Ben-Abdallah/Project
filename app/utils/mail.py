from flask_mail import Message
from flask_mail import Mail

mail = Mail()


def send_email(to, subject, template):
    from app import app
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)
