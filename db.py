"""
Hermes - Database layer (PostgreSQL).

The database is the central hub (see home-services-agents-explained.md Part 3):
every agent reads and writes here. This module owns the connection, schema,
and the simple CRUD helpers the agents use.
"""

import json
import logging
import os
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

log = logging.getLogger("hermes.db")

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Tables created in dependency order (jobs first, then quoting/scheduling/billing).
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id              SERIAL PRIMARY KEY,
    job_ref         TEXT UNIQUE NOT NULL,
    customer_name   TEXT,
    customer_phone  TEXT,
    customer_address TEXT,
    service_type    TEXT,
    urgency         TEXT,
    problem_description TEXT,
    status          TEXT NOT NULL DEFAULT 'incoming',
    source          TEXT NOT NULL DEFAULT 'phone',
    quote_amount    NUMERIC(10,2),
    quote_doc_path  TEXT,
    appointment_at  TIMESTAMPTZ,
    technician_id   INTEGER,
    invoice_id      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quotes (
    id          SERIAL PRIMARY KEY,
    job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    labor_cost  NUMERIC(10,2) NOT NULL DEFAULT 0,
    parts_cost  NUMERIC(10,2) NOT NULL DEFAULT 0,
    dispatch_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
    tax         NUMERIC(10,2) NOT NULL DEFAULT 0,
    total       NUMERIC(10,2) NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'draft',   -- draft | approved | sent | rejected
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS technicians (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    specialties  TEXT[] NOT NULL DEFAULT '{}',
    phone        TEXT,
    max_jobs_per_day INTEGER NOT NULL DEFAULT 3,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS appointments (
    id           SERIAL PRIMARY KEY,
    job_id       INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES technicians(id),
    scheduled_at TIMESTAMPTZ NOT NULL,
    status       TEXT NOT NULL DEFAULT 'scheduled',  -- scheduled | in_progress | done | cancelled
    customer_address TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS invoices (
    id           SERIAL PRIMARY KEY,
    job_id       INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    total        NUMERIC(10,2) NOT NULL,
    status       TEXT NOT NULL DEFAULT 'sent',       -- sent | paid | overdue
    paid_amount  NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at      TIMESTAMPTZ
);
"""


class Database:
    """Thin wrapper over a psycopg connection pool."""

    def __init__(self, url: str = ""):
        self.url = url or DATABASE_URL
        self.available = bool(self.url)

    def connect(self):
        return psycopg.connect(self.url, row_factory=dict_row)

    def init_schema(self):
        if not self.available:
            log.warning("No DATABASE_URL set — skipping schema init")
            return False
        try:
            with self.connect() as conn:
                conn.execute(SCHEMA_SQL)
            log.info("Database schema ready")
            return True
        except Exception as exc:
            log.error("Schema init failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------
    def create_job(self, job: dict) -> dict:
        if not self.available:
            log.info("(no DB) job: %s", job.get("job_ref"))
            return {"job_id": 0, "status": "no_db", "note": "DATABASE_URL not set"}

        job_ref = job.get("job_ref") or f"JOB-{int(datetime.now().timestamp())}"
        with self.connect() as conn:
            row = conn.execute(
                """
                INSERT INTO jobs (job_ref, customer_name, customer_phone,
                                  customer_address, service_type, urgency,
                                  problem_description, status, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, job_ref, status, created_at
                """,
                (
                    job_ref,
                    job.get("customer_name"),
                    job.get("customer_phone"),
                    job.get("customer_address"),
                    job.get("service_type"),
                    job.get("urgency"),
                    job.get("problem_description"),
                    job.get("status", "incoming"),
                    job.get("source", "phone"),
                ),
            ).fetchone()
        log.info("Job created: %s (%s) service=%s urgency=%s",
                 row["job_ref"], row["id"], job.get("service_type"), job.get("urgency"))
        return dict(row)

    def list_jobs(self, limit: int = 50, status: str = "") -> list:
        if not self.available:
            return []
        sql = "SELECT * FROM jobs"
        params = []
        if status:
            sql += " WHERE status = %s"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._serialize(r) for r in rows]

    def get_job(self, job_id: int) -> dict:
        if not self.available:
            return {}
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = %s", (job_id,)).fetchone()
        return self._serialize(row) if row else {}

    def update_job(self, job_id: int, fields: dict) -> bool:
        if not self.available or not fields:
            return False
        cols = ", ".join(f"{k} = %s" for k in fields)
        vals = list(fields.values()) + [job_id]
        with self.connect() as conn:
            cur = conn.execute(
                f"UPDATE jobs SET {cols}, updated_at = now() WHERE id = %s", vals)
            return cur.rowcount > 0

    @staticmethod
    def _serialize(row: dict) -> dict:
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------
    def create_quote(self, quote: dict) -> dict:
        with self.connect() as conn:
            row = conn.execute(
                """
                INSERT INTO quotes (job_id, labor_cost, parts_cost, dispatch_fee,
                                    tax, total, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, job_id, total, status, created_at
                """,
                (
                    quote["job_id"],
                    quote.get("labor_cost", 0),
                    quote.get("parts_cost", 0),
                    quote.get("dispatch_fee", 0),
                    quote.get("tax", 0),
                    quote.get("total", 0),
                    quote.get("status", "draft"),
                ),
            ).fetchone()
        return self._serialize(row)

    def get_quote(self, quote_id: int) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM quotes WHERE id = %s", (quote_id,)).fetchone()
        return self._serialize(row) if row else {}

    def get_quotes_for_job(self, job_id: int) -> list:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM quotes WHERE job_id = %s ORDER BY created_at DESC", (job_id,)
            ).fetchall()
        return [self._serialize(r) for r in rows]

    def update_quote_status(self, quote_id: int, status: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("UPDATE quotes SET status = %s WHERE id = %s",
                               (status, quote_id))
            return cur.rowcount > 0

    def pricing_history(self, service_type: str) -> dict:
        """Average/min/max totals for completed jobs of a service type."""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT quote_amount FROM jobs
                WHERE service_type = %s AND status = 'completed' AND quote_amount IS NOT NULL
                """,
                (service_type,),
            ).fetchall()
        amounts = [float(r["quote_amount"]) for r in rows]
        if not amounts:
            return {"avg": None, "min": None, "max": None, "samples": 0}
        return {"avg": sum(amounts) / len(amounts),
                "min": min(amounts), "max": max(amounts), "samples": len(amounts)}

    # ------------------------------------------------------------------
    # Technicians
    # ------------------------------------------------------------------
    def list_technicians(self, service_type: str = "") -> list:
        with self.connect() as conn:
            if service_type:
                rows = conn.execute(
                    "SELECT * FROM technicians WHERE is_active = TRUE AND %s = ANY(specialties)",
                    (service_type,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM technicians WHERE is_active = TRUE").fetchall()
        return [self._serialize(r) for r in rows]

    def create_technician(self, tech: dict) -> dict:
        with self.connect() as conn:
            row = conn.execute(
                """
                INSERT INTO technicians (name, specialties, phone, max_jobs_per_day)
                VALUES (%s, %s, %s, %s) RETURNING id, name, specialties, phone
                """,
                (tech["name"], tech.get("specialties", []),
                 tech.get("phone"), tech.get("max_jobs_per_day", 3)),
            ).fetchone()
        return self._serialize(row)

    def count_technician_appointments(self, technician_id: int, on_date: str) -> int:
        """How many appointments a technician already has on a date (yyyy-mm-dd)."""
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n FROM appointments
                WHERE technician_id = %s
                  AND scheduled_at::date = %s::date
                  AND status != 'cancelled'
                """,
                (technician_id, on_date),
            ).fetchone()
        return int(row["n"])

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------
    def create_appointment(self, appt: dict) -> dict:
        with self.connect() as conn:
            row = conn.execute(
                """
                INSERT INTO appointments (job_id, technician_id, scheduled_at,
                                          customer_address, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, job_id, technician_id, scheduled_at, status
                """,
                (appt["job_id"], appt.get("technician_id"),
                 appt["scheduled_at"], appt.get("customer_address"),
                 appt.get("status", "scheduled")),
            ).fetchone()
        return self._serialize(row)

    def list_appointments(self, job_id: int = 0, technician_id: int = 0) -> list:
        with self.connect() as conn:
            sql = "SELECT * FROM appointments"
            params = []
            clauses = []
            if job_id:
                clauses.append("job_id = %s")
                params.append(job_id)
            if technician_id:
                clauses.append("technician_id = %s")
                params.append(technician_id)
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY scheduled_at"
            rows = conn.execute(sql, params).fetchall()
        return [self._serialize(r) for r in rows]


db = Database()
