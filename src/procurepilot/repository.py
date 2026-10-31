import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import UUID

from procurepilot.models import Assessment, AssessmentStatus, ReviewDecision


class AssessmentRepository:
    """SQLite-backed audit repository with explicit human-review updates."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._lock = Lock()
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def save(self, assessment: Assessment) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessments (id, status, created_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (
                    str(assessment.id),
                    assessment.status.value,
                    assessment.created_at.isoformat(),
                    assessment.model_dump_json(),
                ),
            )

    def get(self, assessment_id: UUID) -> Assessment | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM assessments WHERE id = ?", (str(assessment_id),)
            ).fetchone()
        return Assessment.model_validate_json(row["payload"]) if row else None

    def list(self, limit: int = 50) -> list[Assessment]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM assessments ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [Assessment.model_validate_json(row["payload"]) for row in rows]

    def review(self, assessment_id: UUID, decision: ReviewDecision) -> Assessment | None:
        assessment = self.get(assessment_id)
        if assessment is None:
            return None
        if assessment.status != AssessmentStatus.PENDING_REVIEW:
            raise ValueError("Only pending assessments can receive a human decision")

        assessment.status = (
            AssessmentStatus.APPROVED if decision.approved else AssessmentStatus.REJECTED
        )
        assessment.reviewed_at = datetime.now(UTC)
        assessment.reviewer = decision.reviewer
        assessment.review_note = decision.note
        self.save(assessment)
        return assessment
