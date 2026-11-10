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


db = Database()
