from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.screening import Screening
from app.models.assessment import Assessment
from app.models.audit import AuditEvent


class ScreeningOrchestrator:
    """Stub orchestrator for Phase 1 that transitions screening state and persists assessment."""

    async def process_screening(self, screening_id: str, db: AsyncSession) -> None:
        stmt = select(Screening).where(Screening.id == screening_id)
        result = await db.execute(stmt)
        screening: Optional[Screening] = result.scalar_one_or_none()

        if not screening:
            return

        # 1. Transition to processing
        screening.status = "processing"
        screening.updated_at = datetime.now(timezone.utc)
        await db.commit()

        # 2. Stub processing pipeline (Phase 1)
        checks = [
            {"name": "ocr", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "mrz_checksum", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "expiry", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "date_consistency", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "format", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "watchlist", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "tamper", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
            {"name": "face", "state": "not_performed", "detail": "Analysis pipeline not yet implemented"},
        ]
        reasons = ["Analysis pipeline not yet implemented"]

        screening.status = "incomplete"
        screening.risk_level = "incomplete"
        screening.risk_score = None
        screening.requires_human_review = True
        screening.checks = checks
        screening.reasons = reasons
        screening.updated_at = datetime.now(timezone.utc)

        # Create Assessment record
        assessment = Assessment(
            screening_id=screening.id,
            risk_score=None,
            risk_level="incomplete",
            requires_human_review=True,
            reasons=reasons,
            summary="Analysis pipeline not yet implemented"
        )
        db.add(assessment)

        # Record AuditEvent
        audit_event = AuditEvent(
            case_id=screening.id,
            screening_id=screening.id,
            actor="system",
            action="INSPECTION_COMPLETED",
            details={
                "status": "incomplete",
                "risk_level": "incomplete",
                "findings_count": 0
            }
        )
        db.add(audit_event)

        await db.commit()

