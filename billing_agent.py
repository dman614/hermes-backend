"""
Hermes - Billing & Follow-up Agent (bonus).

After a job is completed: generate the invoice from the approved quote
(or completed job), track payment, flag overdue invoices for reminders,
and ask for a review once paid. SMS/email delivery is stubbed with logs
until the notification channel (Twilio Messaging) is wired in.
"""

import logging

from db import db

log = logging.getLogger("hermes.billing")


def generate_invoice(job_id: int, total: float | None = None) -> dict:
    """Create an invoice for a completed job."""
    job = db.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    amount = total if total is not None else (job.get("quote_amount") or 0)
    if not amount:
        raise ValueError(f"Job {job_id} has no quote amount to bill against")

    invoice = db.create_invoice(job_id, float(amount), status="sent")
    db.update_job(job_id, {"status": "invoiced", "invoice_id": invoice["id"]})
    log.info("Invoice created: #%s for job %s ($%.2f)",
             invoice["id"], job_id, amount)
    return {
        "invoice": invoice,
        "customer_name": job.get("customer_name"),
        "service_type": job.get("service_type"),
        "amount": float(amount),
        "next_step": "Send invoice + payment link to customer",
        "delivery": "stubbed (Twilio Messaging not wired)",
    }


def record_payment(invoice_id: int, amount: float | None = None) -> dict:
    """Record a payment and mark the invoice paid."""
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")
    paid = amount if amount is not None else float(invoice["total"])
    ok = db.mark_invoice_paid(invoice_id, paid)
    job_id = invoice["job_id"]
    if ok:
        db.update_job(job_id, {"status": "paid"})
    return {"invoice_id": invoice_id, "paid": ok, "amount": paid,
            "job_id": job_id}


def find_overdue(days: int = 3) -> list:
    """Invoices past 'days' with no payment — ready for reminders."""
    overdue = db.overdue_invoices(days=days)
    return [{"invoice_id": inv["id"], "job_id": inv["job_id"],
             "total": float(inv["total"]), "created_at": inv["created_at"]}
            for inv in overdue]


def run_followups(days: int = 3) -> dict:
    """Nightly job: remind on overdue, ask for review on recently paid."""
    overdue = find_overdue(days)
    for item in overdue:
        log.info("REMINDER due for invoice #%s (job %s, $%.2f)",
                 item["invoice_id"], item["job_id"], item["total"])
    # Review requests would query recently-paid invoices here (stubbed).
    return {"reminders_due": len(overdue),
            "reminders": overdue,
            "reviews_requested": 0,
            "delivery": "stubbed"}
