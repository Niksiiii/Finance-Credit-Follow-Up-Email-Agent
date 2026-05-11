"""
Invoice API endpoints.
CRUD operations + CSV/Excel file upload.
"""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Invoice
from ..schemas import InvoiceResponse, InvoiceUpdate, InvoiceCreate
from ..services.data_ingestion import parse_file, ingest_dataframe
from ..services.tone_engine import get_stage_from_days

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


def _enrich_invoice(inv: Invoice) -> dict:
    """Add computed fields (days_overdue, current_stage, balance_amount) to an invoice."""
    days = max(0, (date.today() - inv.due_date).days) if inv.due_date < date.today() else 0
    stage = get_stage_from_days(days) if days > 0 else 0

    # If partially paid (50%+), reduce stage by 1
    if inv.status == "PARTIAL" and inv.balance_amount is not None and stage > 0:
        paid_ratio = 1 - (inv.balance_amount / inv.amount) if inv.amount > 0 else 0
        if paid_ratio >= 0.5:
            stage = max(1, stage - 1)

    data = {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "client_name": inv.client_name,
        "client_email": inv.client_email,
        "amount": inv.amount,
        "due_date": inv.due_date,
        "follow_up_count": inv.follow_up_count,
        "status": inv.status,
        "assigned_to": inv.assigned_to,
        "balance_amount": inv.balance_amount,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "days_overdue": days,
        "current_stage": stage,
    }
    return data


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, PAID, ESCALATED, LEGAL_REVIEW"),
    db: Session = Depends(get_db),
):
    """List all invoices, optionally filtered by status."""
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status.upper())
    invoices = query.order_by(Invoice.due_date.asc()).all()
    return [_enrich_invoice(inv) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get a single invoice by ID."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _enrich_invoice(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: int, update: InvoiceUpdate, db: Session = Depends(get_db)):
    """Update an invoice (e.g., mark as paid, assign to team member)."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if update.status is not None:
        invoice.status = update.status.upper()
    if update.assigned_to is not None:
        invoice.assigned_to = update.assigned_to
    if update.follow_up_count is not None:
        invoice.follow_up_count = update.follow_up_count

    db.commit()
    db.refresh(invoice)
    return _enrich_invoice(invoice)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel file to import invoice records."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or Excel (.xlsx, .xls).",
        )

    content = await file.read()

    # Parse the file
    df, parse_errors = parse_file(content, file.filename)
    if parse_errors:
        raise HTTPException(status_code=400, detail={"errors": parse_errors})

    # Ingest into database
    inserted, skipped, ingest_errors = ingest_dataframe(db, df)

    return {
        "message": "File processed successfully",
        "filename": file.filename,
        "total_rows": len(df),
        "inserted": inserted,
        "skipped_duplicates": skipped,
        "errors": ingest_errors,
    }


@router.delete("/clear")
def clear_all_data(db: Session = Depends(get_db)):
    """Delete ALL invoices, payments, follow-up logs, and responses."""
    from ..models import FollowUpLog, Payment, ResponseTracker, TeamMember
    db.query(FollowUpLog).delete()
    db.query(Payment).delete()
    db.query(ResponseTracker).delete()
    db.query(Invoice).delete()
    db.commit()
    return {"message": "All data cleared successfully"}

