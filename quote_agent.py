"""
Hermes - Quote Generation Agent (Week 3).

Takes a job from the central DB, looks up pricing history, estimates labor,
computes a cost breakdown with tax, stores the quote, and supports the
owner approval flow (draft -> approved -> sent, or rejected).
"""

import logging

from db import db

log = logging.getLogger("hermes.quote")

# Your company's markups (from the explainer doc Part 2)
HOURLY_RATE = 95.0
DISPATCH_FEE = 75.0
TAX_RATE = 0.05  # GST

# Base labor estimates per service type (hours), adjusted by complexity words.
BASE_LABOR_HOURS = {
    "plumbing": {"simple": 1.5, "moderate": 3.0, "complex": 5.0},
    "hvac": {"simple": 2.0, "moderate": 4.0, "complex": 6.0},
    "electrical": {"simple": 2.0, "moderate": 3.5, "complex": 5.0},
}

COMPLEX_WORDS = ("multiple", "complex", "old", "replace", "rewire", "reroute",
                 "panel", "furnace", "boiler", "whole", "extensive", "main")
SIMPLE_WORDS = ("quick", "simple", "small", "minor", "tighten", "filter", "switch")


def estimate_labor_hours(service_type: str, problem_description: str) -> float:
    """Estimate job duration from service type + complexity cues in the text."""
    base = BASE_LABOR_HOURS.get(service_type, {"simple": 2.0, "moderate": 3.0, "complex": 4.0})
    text = (problem_description or "").lower()
    complex_hits = sum(1 for w in COMPLEX_WORDS if w in text)
    simple_hits = sum(1 for w in SIMPLE_WORDS if w in text)
    if complex_hits > simple_hits:
        return base["complex"]
    if simple_hits > 0 and complex_hits == 0:
        return base["simple"]
    return base["moderate"]


def calculate_total_cost(service_type: str, problem_description: str,
                         parts_cost: float = 0.0) -> dict:
    """Full quote math: labor @ HOURLY_RATE, parts, dispatch fee, tax."""
    labor_hours = estimate_labor_hours(service_type, problem_description)
    labor_cost = round(labor_hours * HOURLY_RATE, 2)
    subtotal = round(labor_cost + parts_cost + DISPATCH_FEE, 2)
    tax = round(subtotal * TAX_RATE, 2)
    return {
        "labor_hours": labor_hours,
        "labor_cost": labor_cost,
        "parts_cost": round(parts_cost, 2),
        "dispatch_fee": DISPATCH_FEE,
        "subtotal": subtotal,
        "tax_rate": TAX_RATE,
        "tax": tax,
        "total_with_tax": round(subtotal + tax, 2),
    }


def generate_quote(job_id: int, parts_cost: float = 0.0) -> dict:
    """Generate a quote for a job, informed by pricing history from the DB."""
    job = db.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    history = db.pricing_history(job.get("service_type") or "")
    costs = calculate_total_cost(
        job.get("service_type") or "unknown",
        job.get("problem_description") or "",
        parts_cost,
    )

    quote_row = db.create_quote({
        "job_id": job_id,
        "labor_cost": costs["labor_cost"],
        "parts_cost": costs["parts_cost"],
        "dispatch_fee": costs["dispatch_fee"],
        "tax": costs["tax"],
        "total": costs["total_with_tax"],
        "status": "draft",
    })
    db.update_job(job_id, {"quote_amount": costs["total_with_tax"]})

    return {
        "quote_id": quote_row["id"],
        "job_id": job_id,
        "customer_name": job.get("customer_name"),
        "service_type": job.get("service_type"),
        "urgency": job.get("urgency"),
        "breakdown": costs,
        "pricing_history": history,
        "status": "draft",
        "next_step": "Owner approval required before sending to customer",
    }


def set_quote_status(quote_id: int, status: str) -> dict:
    """Owner approval flow: draft -> approved -> sent, or rejected."""
    if status not in ("approved", "sent", "rejected", "draft"):
        raise ValueError(f"Invalid quote status: {status}")
    ok = db.update_quote_status(quote_id, status)
    quote = db.get_quote(quote_id)
    if ok and quote:
        db.update_job(quote["job_id"], {"status": "quote_sent" if status == "sent"
                                        else "incoming"})
    return {"quote_id": quote_id, "status": status, "updated": ok, "quote": quote}
