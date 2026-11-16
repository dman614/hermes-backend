"""
Hermes - SMS notifications via Twilio Messaging.

Sends SMS to customers and technicians. Fails softly when credentials
are missing or the send fails, so it never breaks the job flow.
"""

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger("hermes.sms")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_FROM", "+17789094293")  # the business line

TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def send_sms(to: str | None, body: str) -> dict:
    """Send a single SMS. Returns {'sent': bool, 'sid': str?, 'error': str?}."""
    if not to:
        return {"sent": False, "error": "no recipient"}
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN):
        log.info("[sms stubbed] to=%s: %s", to, body[:80])
        return {"sent": False, "stubbed": True, "error": "TWILIO creds not set"}

    data = urllib.parse.urlencode({
        "From": TWILIO_FROM,
        "To": to,
        "Body": body,
    }).encode()
    auth = base64.b64encode(
        f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    req = urllib.request.Request(
        TWILIO_API.format(sid=TWILIO_ACCOUNT_SID),
        data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
        log.info("SMS sent to %s (sid=%s)", to, payload.get("sid"))
        return {"sent": True, "sid": payload.get("sid"), "status": payload.get("status")}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        log.error("SMS failed to %s: HTTP %s %s", to, e.code, detail)
        return {"sent": False, "error": f"HTTP {e.code}", "detail": detail}
    except Exception as exc:
        log.error("SMS failed to %s: %s", to, exc)
        return {"sent": False, "error": str(exc)}


def send_customer_confirmation(phone: str | None, tech_name: str, when: str) -> dict:
    body = (f"Comox Valley Home Services: your appointment is confirmed "
            f"for {when} with technician {tech_name}. "
            f"Reply STOP to opt out. See you soon!")
    return send_sms(phone, body)


def send_technician_job_card(phone: str | None, tech_name: str, job_ref: str | None,
                             service_type: str, address: str, when: str) -> dict:
    body = (f"New job card for {tech_name}: {service_type} at {address} "
            f"scheduled {when} (ref {job_ref}). Job details in the dashboard.")
    return send_sms(phone, body)


def send_invoice_notice(phone: str | None, invoice_id: int, amount: float) -> dict:
    body = (f"Comox Valley Home Services: invoice #{invoice_id} for "
            f"${amount:.2f} is ready. A payment link is coming soon; "
            f"if you have questions call us back on this line."
            if phone else None)
    if not body:
        return {"sent": False, "error": "no recipient"}
    return send_sms(phone, body)


def send_payment_confirmation(phone: str | None, invoice_id: int, amount: float) -> dict:
    body = (f"Comox Valley Home Services: payment of ${amount:.2f} for "
            f"invoice #{invoice_id} received. Thank you for your business!")
    return send_sms(phone, body)
