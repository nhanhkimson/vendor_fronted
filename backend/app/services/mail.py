"""Outbound mail: always writes a local mailbox copy; SMTP is optional."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import settings
from app.core.db import utcnow

log = logging.getLogger("bazaar.mail")


def mailbox_dir() -> Path:
    path = settings.private_dir / "mailbox"
    path.mkdir(parents=True, exist_ok=True)
    return path


def send_mail(*, to: str, subject: str, text: str, html: str | None = None) -> str:
    """Send (or simulate) an email. Returns the local mailbox file path."""
    now = utcnow()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    safe_to = "".join(ch if ch.isalnum() or ch in "._@-" else "_" for ch in to)[:80]
    path = mailbox_dir() / f"{stamp}-{safe_to}.eml"

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message["Date"] = now.strftime("%a, %d %b %Y %H:%M:%S +0000")
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    path.write_bytes(message.as_bytes())
    log.info("mail saved to %s · to=%s · subject=%s", path.name, to, subject)

    if settings.smtp_host:
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                if settings.smtp_user:
                    smtp.starttls()
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
            log.info("mail delivered via SMTP to %s", to)
        except Exception:
            log.exception("SMTP send failed for %s — local copy kept at %s", to, path)

    return str(path)
