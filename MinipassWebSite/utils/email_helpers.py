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
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")
    mail.init_app(app)




def send_user_deployment_email(to, url, password, email_info=None):
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

    # Build multipart MIME message with images (NO filenames to prevent attachments)
    multipart = MIMEMultipart('related')
    multipart['Subject'] = subject
    multipart['From'] = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")
    multipart['To'] = to

    # Attach HTML content
    multipart.attach(MIMEText(html, 'html'))

    # Load and attach images as inline (WITHOUT filename parameter)
    images = {
        'welcom4': 'static/image/welcom4.jpg',
        'thumb-youtube': 'static/image/thumb-youtube.jpg'
    }

    for cid, image_path in images.items():
        with open(image_path, 'rb') as f:
            image_data = f.read()
            part = MIMEImage(image_data)
            part.add_header('Content-ID', f'<{cid}>')
            part.add_header('Content-Disposition', 'inline')
            # NO filename header - this prevents Gmail from showing attachment
            multipart.attach(part)

    # Send using smtplib with Flask-Mail's SMTP config
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    smtp_user = os.getenv("MAIL_USERNAME")
    smtp_pass = os.getenv("MAIL_PASSWORD")

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(multipart)




def send_support_error_email(user_email, app_name, error_log):
    subject = f"[MiniPass Deployment Error] {app_name}"
    tech_support = "kdresdell@gmail.com"
    recipients = [user_email]
    cc = [tech_support]

    html_body = f"""
    <p>Hi,</p>
    <p>We encountered an issue while deploying your MiniPass app: <strong>{app_name}</strong>.</p>
    <p>Our technical team has been notified and will investigate shortly. You will receive a follow-up email once the deployment is complete.</p>
    <hr>
    <pre style="background:#f8f9fa;padding:10px;border-radius:5px;font-size:0.9rem;">{error_log}</pre>
    <p>— MiniPass Deployment Bot</p>
    """

    msg = Message(subject=subject, recipients=recipients, cc=cc, html=html_body)
    mail.send(msg)

