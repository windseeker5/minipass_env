# utils/email_helpers.py

from flask import render_template
from flask_mail import Message, Mail
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib


#from app import mail
from utils.mail import mail

def init_mail(app):
    from utils.deploy_helpers import is_production_environment

    if is_production_environment():
        # Production: Use minipass.me mail server
        app.config['MAIL_SERVER'] = os.getenv("PROD_MAIL_SERVER", "mail.minipass.me")
        app.config['MAIL_PORT'] = int(os.getenv("PROD_MAIL_PORT", 587))
        app.config['MAIL_USERNAME'] = os.getenv("PROD_MAIL_USERNAME", "support@minipass.me")
        app.config['MAIL_PASSWORD'] = os.getenv("PROD_MAIL_PASSWORD")
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv("PROD_MAIL_DEFAULT_SENDER", "minipass <support@minipass.me>")
    else:
        # Local dev: Use Gmail
        app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
        app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
        app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")

    app.config['MAIL_USE_TLS'] = True
    mail.init_app(app)




def send_user_deployment_email(to, url, password, email_info=None):
    from utils.deploy_helpers import is_production_environment

    subject = "🎉 Votre application minipass est prête!"  # ✅ French translation

    # ✅ Render with admin email and email info included
    html = render_template(
        "emails/deployment_ready.html",
        url=url,
        password=password,
        user_email=to,
        email_info=email_info
    )

    # Build email body text with email info if available
    body_text = f"Your app is live: {url}\nAdmin Email: {to}\nPassword: {password}"
    if email_info:
        body_text += f"\n\nEmail Account Created:\nEmail: {email_info.get('email_address', 'N/A')}\nPassword: {email_info.get('email_password', 'Same as app password')}"
        if email_info.get('forwarding_setup'):
            body_text += "\nForwarding: Enabled"

    # Select SMTP settings based on environment
    if is_production_environment():
        # Production: Use minipass.me mail server
        smtp_server = os.getenv("PROD_MAIL_SERVER", "mail.minipass.me")
        smtp_port = int(os.getenv("PROD_MAIL_PORT", 587))
        smtp_user = os.getenv("PROD_MAIL_USERNAME", "support@minipass.me")
        smtp_pass = os.getenv("PROD_MAIL_PASSWORD")
        sender = os.getenv("PROD_MAIL_DEFAULT_SENDER", "minipass <support@minipass.me>")
    else:
        # Local dev: Use Gmail
        smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        smtp_user = os.getenv("MAIL_USERNAME")
        smtp_pass = os.getenv("MAIL_PASSWORD")
        sender = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")

    # Build multipart MIME message with images (NO filenames to prevent attachments)
    multipart = MIMEMultipart('related')
    multipart['Subject'] = subject
    multipart['From'] = sender
    multipart['To'] = to

    # Attach HTML content
    multipart.attach(MIMEText(html, 'html'))

    # Load and attach images as inline (WITHOUT filename parameter)
    images = {
        'welcom4': 'static/image/welcom4.jpg',
        'thumb-youtube': 'static/image/thumb-youtube.jpg',
        'discord-icon': 'static/image/discord-icon.png',
        'facebook-icon': 'static/image/facebook-icon.png',
        'instagram-icon': 'static/image/instagram-icon.png',
        'youtube-icon': 'static/image/youtube-icon.png',
        'linkedin-icon': 'static/image/linkedin-icon.png'
    }

    for cid, image_path in images.items():
        with open(image_path, 'rb') as f:
            image_data = f.read()
            part = MIMEImage(image_data)
            part.add_header('Content-ID', f'<{cid}>')
            part.add_header('Content-Disposition', 'inline')
            # NO filename header - this prevents Gmail from showing attachment
            multipart.attach(part)

    # Send using smtplib
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(multipart)




def send_support_error_email(user_email, app_name, error_log):
    subject = f"[minipass Deployment Error] {app_name}"
    tech_support = "kdresdell@gmail.com"
    recipients = [user_email]
    cc = [tech_support]

    html_body = f"""
    <p>Hi,</p>
    <p>We encountered an issue while deploying your minipass app: <strong>{app_name}</strong>.</p>
    <p>Our technical team has been notified and will investigate shortly. You will receive a follow-up email once the deployment is complete.</p>
    <hr>
    <pre style="background:#f8f9fa;padding:10px;border-radius:5px;font-size:0.9rem;">{error_log}</pre>
    <p>— minipass Deployment Bot</p>
    """

    msg = Message(subject=subject, recipients=recipients, cc=cc, html=html_body)
    mail.send(msg)


def send_password_reset_email(to, subdomain, app_url, new_password):
    """
    Send a password reset email to a customer.

    Args:
        to (str): Customer email address
        subdomain (str): Customer's subdomain
        app_url (str): Full URL to the customer's app
        new_password (str): The new password to send
    """
    from utils.deploy_helpers import is_production_environment

    subject = "🔑 Votre mot de passe minipass a été réinitialisé"

    # Render HTML template
    html = render_template(
        "emails/password_reset.html",
        subdomain=subdomain,
        app_url=app_url,
        new_password=new_password,
        user_email=to
    )

    # Select SMTP settings based on environment
    if is_production_environment():
        smtp_server = os.getenv("PROD_MAIL_SERVER", "mail.minipass.me")
        smtp_port = int(os.getenv("PROD_MAIL_PORT", 587))
        smtp_user = os.getenv("PROD_MAIL_USERNAME", "support@minipass.me")
        smtp_pass = os.getenv("PROD_MAIL_PASSWORD")
        sender = os.getenv("PROD_MAIL_DEFAULT_SENDER", "minipass <support@minipass.me>")
    else:
        smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        smtp_user = os.getenv("MAIL_USERNAME")
        smtp_pass = os.getenv("MAIL_PASSWORD")
        sender = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")

    # Build email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to

    # Plain text fallback
    text = f"""
Votre mot de passe minipass a été réinitialisé.

Application: {app_url}
Nouveau mot de passe: {new_password}

Connectez-vous avec votre email ({to}) et ce nouveau mot de passe.

— L'équipe minipass
    """
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

