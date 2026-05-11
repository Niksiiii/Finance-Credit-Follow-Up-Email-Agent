"""
Follow-Up API endpoints.
Trigger the agent, view logs, preview emails.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FollowUpLog, Invoice
from ..schemas import FollowUpLogResponse, EmailPreview, TriggerResult
from ..services.agent import run_follow_up_agent, preview_email_for_invoice
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/followups", tags=["Follow-Ups"])


@router.post("/trigger", response_model=TriggerResult)
def trigger_follow_ups(
    dry_run: Optional[bool] = Query(None, description="Override dry-run setting"),
    db: Session = Depends(get_db),
):
    """
    Run the follow-up agent.
    Scans all overdue invoices and dispatches the appropriate follow-up stage.
    """
    # Use query param if provided, otherwise use global setting
    is_dry_run = dry_run if dry_run is not None else settings.DRY_RUN_MODE

    result = run_follow_up_agent(db, dry_run=is_dry_run)
    return result


@router.get("/logs", response_model=List[FollowUpLogResponse])
def get_follow_up_logs(
    invoice_no: Optional[str] = Query(None),
    stage: Optional[int] = Query(None),
    send_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get follow-up audit logs with optional filters."""
    query = db.query(FollowUpLog).join(Invoice)

    if invoice_no:
        query = query.filter(Invoice.invoice_no == invoice_no)
    if stage is not None:
        query = query.filter(FollowUpLog.stage == stage)
    if send_status:
        query = query.filter(FollowUpLog.send_status == send_status.upper())

    logs = query.order_by(FollowUpLog.sent_at.desc()).offset(offset).limit(limit).all()

    result = []
    for log in logs:
        invoice = db.query(Invoice).filter(Invoice.id == log.invoice_id).first()
        result.append({
            "id": log.id,
            "invoice_id": log.invoice_id,
            "stage": log.stage,
            "tone": log.tone,
            "email_subject": log.email_subject,
            "email_body": log.email_body,
            "send_status": log.send_status,
            "recipient_email": log.recipient_email,
            "sent_at": log.sent_at,
            "error_message": log.error_message,
            "invoice_no": invoice.invoice_no if invoice else None,
            "client_name": invoice.client_name if invoice else None,
            "amount": invoice.amount if invoice else None,
        })

    return result


@router.get("/preview/{invoice_id}", response_model=EmailPreview)
def preview_email(invoice_id: int, db: Session = Depends(get_db)):
    """
    Preview the email that would be generated for a specific invoice.
    Does NOT send or log — purely for review.
    """
    preview = preview_email_for_invoice(db, invoice_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return preview


# ── Automation Scheduler Endpoints ─────────────────────────

@router.post("/automation/start")
def start_automation(
    interval_hours: float = Query(24.0, ge=0.1, le=720, description="Run interval in hours"),
    dry_run: bool = Query(True, description="Dry-run mode for automated emails"),
):
    """
    Start the automated follow-up scheduler.
    The agent will run immediately and then repeat at the specified interval.
    """
    from ..services.scheduler import scheduler
    if scheduler.status["is_running"]:
        raise HTTPException(status_code=400, detail="Automation is already running")

    scheduler.start(interval_hours=interval_hours, dry_run=dry_run)
    return {
        "message": "Automation started",
        "interval_hours": interval_hours,
        "dry_run": dry_run,
        **scheduler.status,
    }


@router.post("/automation/stop")
def stop_automation():
    """Stop the automated follow-up scheduler."""
    from ..services.scheduler import scheduler
    if not scheduler.status["is_running"]:
        raise HTTPException(status_code=400, detail="Automation is not running")

    scheduler.stop()
    return {"message": "Automation stopped", **scheduler.status}


@router.get("/automation/status")
def get_automation_status():
    """Get the current automation scheduler status."""
    from ..services.scheduler import scheduler
    return scheduler.status

