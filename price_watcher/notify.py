"""Envío de alertas por email (SMTP) y por webhook/ntfy.

Toda la configuración sensible se lee de variables de entorno, nunca del
archivo YAML, para que el repositorio no contenga secretos.
"""
from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage

import requests

from .diff import Change


def format_message(changes: list[Change]) -> tuple[str, str]:
    """Devuelve (asunto, cuerpo) en texto plano para las alertas."""
    subject = f"price-watcher: {len(changes)} cambio(s) detectado(s)"
    lines = ["Se detectaron los siguientes cambios:", ""]
    for c in changes:
        lines.append(f"- [{c.kind}] {c.name}: {c.detail}")
        lines.append(f"  {c.url}")
    body = "\n".join(lines)
    return subject, body


def send_email(subject: str, body: str) -> str | None:
    """Envía un correo si las variables SMTP_* están configuradas.

    Devuelve None si se envió, o un string con el motivo si se omitió/falló.
    """
    host = os.getenv("SMTP_HOST")
    to_addr = os.getenv("ALERT_EMAIL_TO")
    if not host or not to_addr:
        return "email omitido (faltan SMTP_HOST o ALERT_EMAIL_TO)"
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    from_addr = os.getenv("ALERT_EMAIL_FROM", user or "price-watcher@localhost")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if port == 587:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
    except Exception as exc:  # noqa: BLE001 - reportamos el motivo al usuario
        return f"email falló: {exc}"
    return None


def send_webhook(subject: str, body: str) -> str | None:
    """POST a un webhook genérico (JSON) y/o a un topic de ntfy (texto plano)."""
    results: list[str] = []

    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        try:
            resp = requests.post(
                webhook_url,
                json={"title": subject, "message": body},
                timeout=20,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            results.append(f"webhook falló: {exc}")

    ntfy_topic = os.getenv("NTFY_TOPIC")
    if ntfy_topic:
        server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
        try:
            resp = requests.post(
                f"{server}/{ntfy_topic}",
                data=body.encode("utf-8"),
                headers={"Title": subject, "Tags": "money_with_wings"},
                timeout=20,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            results.append(f"ntfy falló: {exc}")

    if not webhook_url and not ntfy_topic:
        return "webhook/ntfy omitido (faltan WEBHOOK_URL o NTFY_TOPIC)"
    return "; ".join(results) if results else None


def notify(changes: list[Change]) -> list[str]:
    """Envía las alertas disponibles. Devuelve una lista de mensajes de estado."""
    if not changes:
        return ["sin cambios: no se envían alertas"]
    subject, body = format_message(changes)
    status: list[str] = []
    for fn in (send_email, send_webhook):
        result = fn(subject, body)
        status.append(result if result else f"{fn.__name__}: enviado")
    return status
