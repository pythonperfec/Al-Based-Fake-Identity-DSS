from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user, require_role, get_storage, get_queue
from app.domain.interfaces import IObjectStorage, IJobQueue
from app.domain.schemas import (
    ScreeningCreateResponse,
    ScreeningsListResponse,
    ScreeningSummary,
    ScreeningDetail,
    FindingsListResponse,
    FindingResponse,
    ReviewCreate,
    ReviewResponse,
)
from app.models.user import User
from app.models.screening import Screening, Review
from app.models.document import Document
from app.models.finding import Finding
from app.models.audit import AuditEvent

router = APIRouter(prefix="/screenings", tags=["Screenings"])


def mask_document_number(fields: dict) -> dict:
    masked = dict(fields)
    doc_num = masked.get("document_number")
    if doc_num and isinstance(doc_num, str):
        if len(doc_num) > 4:
            masked["document_number"] = "*" * (len(doc_num) - 4) + doc_num[-4:]
        else:
            masked["document_number"] = "****"
    return masked


@router.post("", response_model=ScreeningCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_screening(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: IObjectStorage = Depends(get_storage),
    queue: IJobQueue = Depends(get_queue),
):
    # 1. Validate Idempotency-Key Header
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "IDEMPOTENCY_KEY_REQUIRED", "message": "Idempotency-Key header is required"}
        )

    # 2. Validate Document Type
    if document_type not in ["passport", "national_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_DOCUMENT_TYPE",
                "message": f"Unsupported document type '{document_type}'. Allowed types: 'passport', 'national_id'"
            }
        )

    # 3. Idempotency Replay Check
    existing_stmt = select(Screening).where(
        Screening.idempotency_key == idempotency_key,
        Screening.user_id == current_user.id
    )
    existing_res = await db.execute(existing_stmt)
    existing_screening = existing_res.scalar_one_or_none()
    if existing_screening:
        return ScreeningCreateResponse(
            screening_id=existing_screening.id,
            status=existing_screening.status,
            document_type=existing_screening.document_type,
            created_at=existing_screening.created_at
        )

    # 4. Validate Content Type
    content_type = file.content_type or ""
    if content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"Media type '{content_type}' is not supported. Allowed: {', '.join(settings.ALLOWED_MIME_TYPES)}"
            }
        )

    # 5. Read File and Validate Size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "PAYLOAD_TOO_LARGE",
                "message": f"File size {file_size} bytes exceeds maximum limit of {settings.MAX_FILE_SIZE_BYTES} bytes"
            }
        )

    # 6. Store File
    filename = file.filename or "upload"
    storage_key, sha256_checksum = await storage.store(file_bytes, filename, content_type)

    # 7. Create Screening Record
    screening = Screening(
        idempotency_key=idempotency_key,
        user_id=current_user.id,
        document_type=document_type,
        status="queued",
        risk_level=None,
        risk_score=None,
        requires_human_review=False,
        extracted_fields={},
        checks=[],
        reasons=[],
    )
    db.add(screening)
    await db.flush()

    # 8. Create Document Record
    document = Document(
        screening_id=screening.id,
        filename=filename,
        content_type=content_type,
        file_size_bytes=file_size,
        storage_key=storage_key,
        sha256_checksum=sha256_checksum,
    )
    db.add(document)

    # 9. Record Initial Audit Event
    audit_event = AuditEvent(
        case_id=screening.id,
        screening_id=screening.id,
        actor=current_user.username,
        action="SCREENING_SUBMITTED",
        details={
            "document_type": document_type,
            "filename": filename,
            "file_size_bytes": file_size,
        }
    )
    db.add(audit_event)

    await db.commit()
    await db.refresh(screening)

    # 10. Enqueue Background Processing Job
    await queue.enqueue(screening.id)

    return ScreeningCreateResponse(
        screening_id=screening.id,
        status=screening.status,
        document_type=screening.document_type,
        created_at=screening.created_at
    )


@router.get("", response_model=ScreeningsListResponse)
async def list_screenings(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Screening)
    count_query = select(func.count(Screening.id))

    if status:
        query = query.where(Screening.status == status)
        count_query = count_query.where(Screening.status == status)
    if risk_level:
        query = query.where(Screening.risk_level == risk_level)
        count_query = count_query.where(Screening.risk_level == risk_level)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(desc(Screening.created_at)).offset(offset).limit(limit)
    res = await db.execute(query)
    screenings = res.scalars().all()

    items = []
    for s in screenings:
        # Enforce null rules on summary
        s_risk_level = None if s.status in ["queued", "processing"] else s.risk_level
        s_risk_score = None if s.status in ["queued", "processing", "failed"] else s.risk_score
        items.append(ScreeningSummary(
            screening_id=s.id,
            status=s.status,
            risk_level=s_risk_level,
            risk_score=s_risk_score,
            requires_human_review=s.requires_human_review,
            document_type=s.document_type,
            created_at=s.created_at,
            updated_at=s.updated_at
        ))

    return ScreeningsListResponse(total=total, items=items)


@router.get("/{id}", response_model=ScreeningDetail)
async def get_screening(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Screening).where(Screening.id == id)
    result = await db.execute(stmt)
    screening = result.scalar_one_or_none()

    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Screening '{id}' not found"}
        )

    # Fetch latest review
    review_stmt = select(Review).where(Review.screening_id == id).order_by(desc(Review.reviewed_at)).limit(1)
    rev_res = await db.execute(review_stmt)
    latest_review = rev_res.scalar_one_or_none()

    review_dto = None
    if latest_review:
        review_dto = ReviewResponse(
            review_id=latest_review.id,
            screening_id=latest_review.screening_id,
            decision=latest_review.decision,
            notes=latest_review.notes,
            reviewed_by=latest_review.reviewed_by,
            reviewed_at=latest_review.reviewed_at
        )

    # Null rules enforcement
    s_risk_level = None if screening.status in ["queued", "processing"] else screening.risk_level
    s_risk_score = None if screening.status in ["queued", "processing", "failed"] else screening.risk_score
    if screening.status == "failed":
        s_risk_level = "incomplete"

    return ScreeningDetail(
        screening_id=screening.id,
        status=screening.status,
        risk_level=s_risk_level,
        risk_score=s_risk_score,
        requires_human_review=screening.requires_human_review,
        document_type=screening.document_type,
        extracted_fields=mask_document_number(screening.extracted_fields or {}),
        checks=screening.checks or [],
        reasons=screening.reasons or [],
        review=review_dto,
        created_at=screening.created_at,
        updated_at=screening.updated_at
    )


@router.get("/{id}/findings", response_model=FindingsListResponse)
async def get_screening_findings(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Screening).where(Screening.id == id)
    res = await db.execute(stmt)
    screening = res.scalar_one_or_none()
    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Screening '{id}' not found"}
        )

    findings_stmt = select(Finding).where(Finding.screening_id == id).order_by(Finding.created_at)
    findings_res = await db.execute(findings_stmt)
    findings = findings_res.scalars().all()

    # Log audit event
    audit_event = AuditEvent(
        case_id=id,
        screening_id=id,
        actor=current_user.username,
        action="FINDINGS_VIEWED",
        details={"screening_id": id}
    )
    db.add(audit_event)
    await db.commit()

    return FindingsListResponse(
        screening_id=id,
        findings=[
            FindingResponse(
                finding_id=f.id,
                type=f.type,
                severity=f.severity,
                reason=f.reason,
                source=f.source,
                evidence_ref=f.evidence_ref
            )
            for f in findings
        ]
    )


@router.get("/{id}/findings/{finding_id}/evidence")
async def get_finding_evidence(
    id: str,
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: IObjectStorage = Depends(get_storage),
):
    stmt = select(Finding).where(Finding.id == finding_id, Finding.screening_id == id)
    res = await db.execute(stmt)
    finding = res.scalar_one_or_none()
    if not finding or not finding.evidence_ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Evidence asset for finding '{finding_id}' not found"}
        )

    try:
        data, content_type = await storage.retrieve(finding.evidence_ref)
        return Response(content=data, media_type=content_type, headers={"Cache-Control": "private, no-store"})
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Evidence image asset missing from storage"}
        )


@router.get("/{id}/image")
async def get_screening_image(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: IObjectStorage = Depends(get_storage),
):
    doc_stmt = select(Document).where(Document.screening_id == id).limit(1)
    doc_res = await db.execute(doc_stmt)
    doc = doc_res.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Document image for screening '{id}' not found"}
        )

    try:
        data, content_type = await storage.retrieve(doc.storage_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Document image asset missing from storage"}
        )

    # Log audit event
    audit_event = AuditEvent(
        case_id=id,
        screening_id=id,
        actor=current_user.username,
        action="IMAGE_VIEWED",
        details={"screening_id": id, "filename": doc.filename}
    )
    db.add(audit_event)
    await db.commit()

    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "private, no-store"}
    )


@router.post("/{id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(require_role("officer")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Screening).where(Screening.id == id)
    res = await db.execute(stmt)
    screening = res.scalar_one_or_none()
    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Screening '{id}' not found"}
        )

    review = Review(
        screening_id=id,
        user_id=current_user.id,
        decision=review_data.decision,
        notes=review_data.notes,
        reviewed_by=current_user.username
    )
    db.add(review)

    audit_event = AuditEvent(
        case_id=id,
        screening_id=id,
        actor=current_user.username,
        action="HUMAN_REVIEW_RECORDED",
        details={
            "review_id": review.id,
            "decision": review_data.decision,
        }
    )
    db.add(audit_event)

    await db.commit()
    await db.refresh(review)

    return ReviewResponse(
        review_id=review.id,
        screening_id=review.screening_id,
        decision=review.decision,
        notes=review.notes,
        reviewed_by=review.reviewed_by,
        reviewed_at=review.reviewed_at
    )
