from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user
from app.domain.schemas import CaseAuditResponse, AuditEventResponse
from app.models.user import User
from app.models.audit import AuditEvent

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("/{id}/audit", response_model=CaseAuditResponse)
async def get_case_audit(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditEvent).where(AuditEvent.case_id == id).order_by(AuditEvent.timestamp)
    res = await db.execute(stmt)
    events = res.scalars().all()

    return CaseAuditResponse(
        case_id=id,
        events=[
            AuditEventResponse(
                event_id=e.id,
                timestamp=e.timestamp,
                actor=e.actor,
                action=e.action,
                details=e.details or {}
            )
            for e in events
        ]
    )

