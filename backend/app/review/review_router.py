from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.dependencies import get_current_operator
from app.models.operator import Operator
from app.review.database import get_db
from app.review.review_service import ReviewService
from app.review.review_repository import ReviewRepository
from app.review.review_schemas import CorrectionPayload, ActionResponse, ReviewSessionOut
from app.review.websocket import review_manager

router = APIRouter(prefix="/review", tags=["Review & HITL"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await review_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real app, handle incoming ws commands here
    except WebSocketDisconnect:
        review_manager.disconnect(websocket)


@router.get("/inbox", response_model=List[ReviewSessionOut])
def get_inbox(db: Session = Depends(get_db), _operator: Operator = Depends(get_current_operator)):
    """Retrieve all pending tasks assigned to the queue."""
    repo = ReviewRepository(db)
    return repo.get_inbox()


@router.get("/{claim_id}", response_model=ReviewSessionOut)
def get_review_session(
    claim_id: str,
    db: Session = Depends(get_db),
    _operator: Operator = Depends(get_current_operator),
):
    repo = ReviewRepository(db)
    session = repo.get_session(claim_id)
    return session


@router.post("/{claim_id}/lock", response_model=ActionResponse)
def lock_session(
    claim_id: str,
    operator_id: str,
    db: Session = Depends(get_db),
    _operator: Operator = Depends(get_current_operator),
):
    service = ReviewService(db)
    return service.lock_claim(claim_id, operator_id)


@router.post("/{claim_id}/unlock", response_model=ActionResponse)
def unlock_session(
    claim_id: str,
    operator_id: str,
    db: Session = Depends(get_db),
    _operator: Operator = Depends(get_current_operator),
):
    service = ReviewService(db)
    return service.unlock_claim(claim_id, operator_id)


@router.post("/{claim_id}/correct", response_model=ActionResponse)
def correct_entity(
    claim_id: str,
    operator_id: str,
    payload: CorrectionPayload,
    db: Session = Depends(get_db),
    _operator: Operator = Depends(get_current_operator),
):
    service = ReviewService(db)
    return service.apply_correction(claim_id, operator_id, payload)


@router.post("/{claim_id}/approve", response_model=ActionResponse)
def approve_claim(
    claim_id: str,
    operator_id: str,
    reason: str,
    db: Session = Depends(get_db),
    _operator: Operator = Depends(get_current_operator),
):
    service = ReviewService(db)
    return service.finalize_review(claim_id, operator_id, "APPROVED", reason)
