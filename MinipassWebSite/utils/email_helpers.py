# utils/email_helpers.py

from flask import render_template
from flask_mail import Message, Mail
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime, timezone
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

    subject = "Votre application minipass - Informations de connexion"  # Transactional subject

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

    # Build multipart/alternative MIME message (RFC 5322 compliant — no embedded images)
    multipart = MIMEMultipart('alternative')
    multipart['Subject'] = subject
    multipart['From'] = sender
    multipart['To'] = to
    multipart['Return-Path'] = sender
    multipart['Date'] = formatdate(localtime=True)
    multipart['Message-ID'] = f"<{int(datetime.now(timezone.utc).timestamp() * 1000000)}@minipass.me>"
    multipart['Auto-Submitted'] = "auto-generated"

    # Plain-text fallback first (RFC 2046: preferred part must be last)
    multipart.attach(MIMEText(body_text, 'plain', 'utf-8'))
    # HTML part last (preferred by mail clients)
    multipart.attach(MIMEText(html, 'html', 'utf-8'))

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


def send_deployment_success_email(user_email, app_name, success_details):
    subject = f"[minipass] New Customer Deployed Successfully: {app_name}"
    tech_support = "kdresdell@gmail.com"
    recipients = [user_email]
    cc = [tech_support]

    html_body = f"""
    <p>🎉 <strong>Great news!</strong></p>
    <p>Your minipass app <strong>{app_name}</strong> has been deployed successfully!</p>
    <hr>
    <pre style="background:#e8f5e8;padding:10px;border-radius:5px;font-size:0.9rem;border:1px solid #4caf50;">{success_details}</pre>
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

    subject = "minipass - Vos informations de connexion"

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
    msg['Return-Path'] = sender
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = f"<{int(datetime.now(timezone.utc).timestamp() * 1000000)}@minipass.me>"
    msg['Auto-Submitted'] = "auto-generated"

    # Plain text fallback
    text = f"""minipass - Vos informations de connexion

L'accès a votre application minipass a ete mis a jour.

Application: {app_url}
Courriel: {to}
Identifiant d'acces: {new_password}

Accedez a votre application avec ces informations.

-- L'equipe minipass
minipass Inc. - Rimouski, QC, Canada
minipass.me
    """
    msg.attach(MIMEText(text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

