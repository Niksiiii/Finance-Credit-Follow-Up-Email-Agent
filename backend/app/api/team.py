"""
Team & Response Tracker API endpoints.
Manage finance team members and track client responses.
"""

from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TeamMember, ResponseTracker, Invoice, Payment
from ..schemas import (
    TeamMemberCreate, TeamMemberResponse,
    ResponseCreate, ResponseUpdate, ResponseResponse,
    PaymentCreate, PaymentResponse,
)
from ..services.agent import process_payment_and_thank
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api", tags=["Team & Responses"])


# ── Team Member Endpoints ──────────────────────────────────

@router.get("/team", response_model=List[TeamMemberResponse])
def list_team_members(db: Session = Depends(get_db)):
    """List all finance team members."""
    return db.query(TeamMember).filter(TeamMember.is_active == True).all()


@router.post("/team", response_model=TeamMemberResponse)
def add_team_member(member: TeamMemberCreate, db: Session = Depends(get_db)):
    """Add a new finance team member."""
    existing = db.query(TeamMember).filter(TeamMember.email == member.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Team member with this email already exists")

    new_member = TeamMember(
        name=member.name,
        email=member.email,
        role=member.role,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


@router.delete("/team/{member_id}")
def deactivate_team_member(member_id: int, db: Session = Depends(get_db)):
    """Deactivate a team member (soft delete)."""
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    member.is_active = False
    db.commit()
    return {"message": f"Team member {member.name} deactivated"}


# ── Response Tracker Endpoints ──────────────────────────────

@router.get("/responses", response_model=List[ResponseResponse])
def list_responses(
    action_status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all client responses with optional filters."""
    query = db.query(ResponseTracker).join(Invoice)

    if action_status:
        query = query.filter(ResponseTracker.action_status == action_status.upper())
    if assigned_to:
        query = query.filter(ResponseTracker.assigned_to == assigned_to)

    responses = query.order_by(ResponseTracker.updated_at.desc()).all()

    result = []
    for resp in responses:
        invoice = db.query(Invoice).filter(Invoice.id == resp.invoice_id).first()
        result.append({
            "id": resp.id,
            "invoice_id": resp.invoice_id,
            "response_type": resp.response_type,
            "notes": resp.notes,
            "assigned_to": resp.assigned_to,
            "action_status": resp.action_status,
            "created_at": resp.created_at,
            "updated_at": resp.updated_at,
            "invoice_no": invoice.invoice_no if invoice else None,
            "client_name": invoice.client_name if invoice else None,
        })

    return result


@router.post("/responses", response_model=ResponseResponse)
def create_response(resp: ResponseCreate, db: Session = Depends(get_db)):
    """Log a new client response."""
    invoice = db.query(Invoice).filter(Invoice.id == resp.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    new_resp = ResponseTracker(
        invoice_id=resp.invoice_id,
        response_type=resp.response_type.upper(),
        notes=resp.notes,
        assigned_to=resp.assigned_to,
    )
    db.add(new_resp)
    db.commit()
    db.refresh(new_resp)

    return {
        "id": new_resp.id,
        "invoice_id": new_resp.invoice_id,
        "response_type": new_resp.response_type,
        "notes": new_resp.notes,
        "assigned_to": new_resp.assigned_to,
        "action_status": new_resp.action_status,
        "created_at": new_resp.created_at,
        "updated_at": new_resp.updated_at,
        "invoice_no": invoice.invoice_no,
        "client_name": invoice.client_name,
    }


@router.patch("/responses/{response_id}", response_model=ResponseResponse)
def update_response(
    response_id: int,
    update: ResponseUpdate,
    db: Session = Depends(get_db),
):
    """Update a response (status, assignment, notes)."""
    resp = db.query(ResponseTracker).filter(ResponseTracker.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")

    if update.action_status is not None:
        resp.action_status = update.action_status.upper()
    if update.assigned_to is not None:
        resp.assigned_to = update.assigned_to
    if update.notes is not None:
        resp.notes = update.notes

    resp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resp)

    invoice = db.query(Invoice).filter(Invoice.id == resp.invoice_id).first()

    return {
        "id": resp.id,
        "invoice_id": resp.invoice_id,
        "response_type": resp.response_type,
        "notes": resp.notes,
        "assigned_to": resp.assigned_to,
        "action_status": resp.action_status,
        "created_at": resp.created_at,
        "updated_at": resp.updated_at,
        "invoice_no": invoice.invoice_no if invoice else None,
        "client_name": invoice.client_name if invoice else None,
    }


# ── Payment Endpoints ──────────────────────────────────────

@router.post("/payments", response_model=dict)
def record_payment(
    payment_data: PaymentCreate,
    dry_run: bool = Query(True, description="When false, actually sends the thank-you email"),
    db: Session = Depends(get_db),
):
    """
    Record a payment and auto-send a thank-you email.
    If partial, sends thank-you with balance amount.
    """
    invoice = db.query(Invoice).filter(Invoice.id == payment_data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    payment = Payment(
        invoice_id=payment_data.invoice_id,
        amount_received=payment_data.amount_received,
        payment_date=payment_data.payment_date,
        payment_reference=payment_data.payment_reference,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Send thank-you email (handles partial vs full)
    thank_result = process_payment_and_thank(
        db, payment, invoice,
        dry_run=dry_run,
    )

    return {
        "message": "Payment recorded successfully",
        "payment_id": payment.id,
        "invoice_no": invoice.invoice_no,
        "amount_received": payment.amount_received,
        "is_partial": thank_result.get("is_partial", False),
        "balance_remaining": thank_result.get("balance_remaining", 0),
        "invoice_status": invoice.status,
        "thank_you": thank_result,
    }


@router.get("/payments", response_model=List[PaymentResponse])
def list_payments(db: Session = Depends(get_db)):
    """List all recorded payments."""
    payments = db.query(Payment).order_by(Payment.created_at.desc()).all()

    result = []
    for p in payments:
        invoice = db.query(Invoice).filter(Invoice.id == p.invoice_id).first()
        result.append({
            "id": p.id,
            "invoice_id": p.invoice_id,
            "amount_received": p.amount_received,
            "payment_date": p.payment_date,
            "payment_reference": p.payment_reference,
            "is_partial": p.is_partial,
            "balance_remaining": p.balance_remaining,
            "thank_you_sent": p.thank_you_sent,
            "created_at": p.created_at,
            "invoice_no": invoice.invoice_no if invoice else None,
            "client_name": invoice.client_name if invoice else None,
            "original_amount": invoice.amount if invoice else None,
        })

    return result
