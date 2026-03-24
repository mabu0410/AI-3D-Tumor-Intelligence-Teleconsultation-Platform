"""
Module 7 — Notification Service
Sends SMS (Twilio) and Push Notifications (Firebase FCM).
Gracefully degrades to logging if credentials are not configured.
"""
import os
from datetime import datetime
from loguru import logger
from app.core.config import settings


# ─── SMS via Twilio ──────────────────────────────────────────────────────────

def send_sms(to_phone: str, body: str) -> dict:
    """
    Send an SMS notification via Twilio.
    Falls back to logger.info() if credentials are not set.
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.info(f"[SMS-MOCK] To: {to_phone} | {body}")
        return {"status": "mock", "to": to_phone, "body": body}

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone,
        )
        logger.info(f"[SMS] Sent to {to_phone}: SID={message.sid}")
        return {"status": "sent", "sid": message.sid, "to": to_phone}
    except Exception as e:
        logger.error(f"[SMS] Failed to send to {to_phone}: {e}")
        return {"status": "error", "error": str(e)}


# ─── Push via Firebase FCM ────────────────────────────────────────────────────

def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None) -> dict:
    """
    Send a push notification via Firebase Cloud Messaging.
    Falls back to logger.info() if Firebase is not configured.
    """
    firebase_config = os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT if hasattr(settings, "FIREBASE_SERVICE_ACCOUNT") else "")

    if not firebase_config:
        logger.info(f"[PUSH-MOCK] Token: {fcm_token[:16]}... | {title}: {body}")
        return {"status": "mock", "title": title, "body": body}

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT)
            firebase_admin.initialize_app(cred)

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=fcm_token,
        )
        response = messaging.send(message)
        logger.info(f"[PUSH] Sent: {response}")
        return {"status": "sent", "message_id": response}
    except Exception as e:
        logger.error(f"[PUSH] Failed: {e}")
        return {"status": "error", "error": str(e)}


# ─── Email (simple SMTP fallback) ─────────────────────────────────────────────

def send_email_notification(to_email: str, subject: str, html_body: str) -> dict:
    """Simple email via SMTP (configured via environment variables)."""
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_host:
        logger.info(f"[EMAIL-MOCK] To: {to_email} | {subject}")
        return {"status": "mock", "to": to_email, "subject": subject}

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL(smtp_host, 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())

        logger.info(f"[EMAIL] Sent to {to_email}: {subject}")
        return {"status": "sent", "to": to_email}
    except Exception as e:
        logger.error(f"[EMAIL] Failed: {e}")
        return {"status": "error", "error": str(e)}
