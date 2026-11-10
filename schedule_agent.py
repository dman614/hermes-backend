"""
Hermes - Scheduling Agent (Week 4).

Picks the best available technician for a job and books the appointment:
1. Find active technicians qualified for the service type
2. Filter out those at their daily job cap
3. Prefer the least-loaded technician (with more hires this becomes
   distance scoring per the explainer doc)
4. Create the appointment, update the job status
"""

import logging
from datetime import datetime, time as dtime

from db import db

log = logging.getLogger("hermes.schedule")


def _parse_datetime(when: str) -> datetime:
    """Accept 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM', or full ISO; default 09:00."""
    text = when.strip() if when else ""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.combine(datetime.now().date(), dtime(9, 0))


def find_available_technicians(service_type: str, on_date: str) -> list:
    """Qualified techs who still have room on their day."""
    techs = db.list_technicians(service_type=service_type)
    available = []
    for t in techs:
        booked = db.count_technician_appointments(t["id"], on_date)
        if booked < (t.get("max_jobs_per_day") or 3):
            available.append({**t, "already_booked": booked})
    return available


def schedule_job(job_id: int, when: str = "", technician_id: int = 0) -> dict:
    """Book the best available technician for the job."""
    job = db.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    service_type = job.get("service_type") or "unknown"
    scheduled_at = _parse_datetime(when)
    on_date = scheduled_at.date().isoformat()

    techs = find_available_technicians(service_type, on_date)
    if not techs:
        return {"success": False,
                "message": "No technician available for that service/date",
                "suggested": "Try another date or add a technician"}

    if technician_id:
        chosen = next((t for t in techs if t["id"] == technician_id), None)
        if not chosen:
            return {"success": False,
                    "message": f"Technician {technician_id} unavailable for {service_type} on {on_date}"}
    else:
        # Least-loaded, then first by id for determinism
        chosen = min(techs, key=lambda t: (t["already_booked"], t["id"]))

    appt = db.create_appointment({
        "job_id": job_id,
        "technician_id": chosen["id"],
        "scheduled_at": scheduled_at.isoformat(),
        "customer_address": job.get("customer_address"),
        "status": "scheduled",
    })
    db.update_job(job_id, {"status": "scheduled",
                           "appointment_at": scheduled_at.isoformat(),
                           "technician_id": chosen["id"]})

    log.info("Job %s scheduled: tech %s at %s", job_id, chosen["name"], scheduled_at)
    return {
        "success": True,
        "appointment": appt,
        "technician": {"id": chosen["id"], "name": chosen["name"],
                       "specialties": chosen.get("specialties", [])},
        "when": scheduled_at.isoformat(),
        "job_status": "scheduled",
        "next_step": "Customer + technician SMS confirmations (Week 4.5)",
    }
