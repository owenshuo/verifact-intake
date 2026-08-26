from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import UUID

from verifact_intake.domain.run import IntakeRun


class SQLiteRunRepository:
    """SQLite authority with append-only review and audit evidence tables."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @classmethod
    def from_url(cls, url: str) -> SQLiteRunRepository:
        prefix = "sqlite:///"
        if not url.startswith(prefix):
            raise ValueError("Only sqlite:/// database URLs are supported in the demo")
        return cls(Path(url.removeprefix(prefix)))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS intake_runs (
                    id TEXT PRIMARY KEY,
                    dataset TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    state_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS review_decisions (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES intake_runs(id),
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS effective_facts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES intake_runs(id),
                    fact_key TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(run_id, fact_key, version)
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    run_id TEXT NOT NULL REFERENCES intake_runs(id),
                    sequence INTEGER NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(run_id, sequence)
                );
                CREATE TRIGGER IF NOT EXISTS review_decisions_no_update
                BEFORE UPDATE ON review_decisions
                BEGIN SELECT RAISE(ABORT, 'review decisions are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS review_decisions_no_delete
                BEFORE DELETE ON review_decisions
                BEGIN SELECT RAISE(ABORT, 'review decisions are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS audit_events_no_update
                BEFORE UPDATE ON audit_events
                BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
                BEFORE DELETE ON audit_events
                BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
                """
            )

    def save(self, run: IntakeRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO intake_runs(id, dataset, created_at, state_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET state_json = excluded.state_json
                """,
                (str(run.id), run.dataset, run.created_at.isoformat(), run.model_dump_json()),
            )
            for decision in run.reviews:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO review_decisions(id, run_id, payload_json)
                    VALUES (?, ?, ?)
                    """,
                    (str(decision.id), str(run.id), decision.model_dump_json()),
                )
            for fact in run.facts:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO effective_facts(
                        id, run_id, fact_key, version, payload_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(fact.id),
                        str(run.id),
                        fact.fact_key,
                        fact.version,
                        fact.model_dump_json(),
                    ),
                )
            for event in run.audit_events:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO audit_events(
                        run_id, sequence, event_hash, payload_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(run.id),
                        event.sequence,
                        event.event_hash,
                        event.model_dump_json(),
                    ),
                )

    def get(self, run_id: UUID) -> IntakeRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM intake_runs WHERE id = ?", (str(run_id),)
            ).fetchone()
        return IntakeRun.model_validate_json(row[0]) if row is not None else None

    def list(self) -> tuple[IntakeRun, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT state_json FROM intake_runs ORDER BY created_at DESC"
            ).fetchall()
        return tuple(IntakeRun.model_validate_json(row[0]) for row in rows)
