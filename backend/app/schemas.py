"""
Pydantic schemas for API request / response validation.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ──────────────────────────────────────────────
# Invoice Schemas
# ──────────────────────────────────────────────

class InvoiceBase(BaseModel):
    invoice_no: str
    client_name: str
    client_email: str
    amount: float
    due_date: date


class InvoiceCreate(InvoiceBase):
    follow_up_count: int = 0
    status: str = "PENDING"


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    follow_up_count: Optional[int] = None


class InvoiceResponse(InvoiceBase):
    id: int
    follow_up_count: int
    status: str
    assigned_to: Optional[str]
    balance_amount: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    days_overdue: Optional[int] = None
    current_stage: Optional[int] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Follow-Up Log Schemas
# ──────────────────────────────────────────────

class FollowUpLogResponse(BaseModel):
    id: int
    invoice_id: int
    stage: int
    tone: str
    email_subject: str
    email_body: str
    send_status: str
    recipient_email: str
    sent_at: datetime
    error_message: Optional[str]

    # Joined fields (optional, for display)
    invoice_no: Optional[str] = None
    client_name: Optional[str] = None
    amount: Optional[float] = None

    class Config:
        from_attributes = True


class EmailPreview(BaseModel):
    """Preview of a generated email (not yet sent)."""
    invoice_no: str
    client_name: str
    stage: int
    tone: str
    subject: str
    body: str
    days_overdue: int


class TriggerResult(BaseModel):
    """Result of running the follow-up agent."""
    total_processed: int
    emails_sent: int
    emails_dry_run: int
    emails_failed: int
    escalated_to_legal: int
    details: List[dict]


# ──────────────────────────────────────────────
# Payment Schemas
# ──────────────────────────────────────────────

class PaymentCreate(BaseModel):
    invoice_id: int
    amount_received: float
    payment_date: date
    payment_reference: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount_received: float
    payment_date: date
    payment_reference: Optional[str]
    is_partial: bool = False
    balance_remaining: Optional[float] = None
    thank_you_sent: bool
    created_at: datetime

    # Joined
    invoice_no: Optional[str] = None
    client_name: Optional[str] = None
    original_amount: Optional[float] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Automation Schemas
# ──────────────────────────────────────────────

class AutomationStatus(BaseModel):
    is_running: bool
    interval_hours: float
    dry_run: bool
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    total_runs: int = 0


# ──────────────────────────────────────────────
# Team Member Schemas
# ──────────────────────────────────────────────

class TeamMemberCreate(BaseModel):
    name: str
    email: str
    role: str = "Executive"


class TeamMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Response Tracker Schemas
# ──────────────────────────────────────────────

class ResponseCreate(BaseModel):
    invoice_id: int
    response_type: str  # PROMISE_TO_PAY | DISPUTE | PARTIAL_PAYMENT | NO_RESPONSE
    notes: Optional[str] = None
    assigned_to: Optional[str] = None


class ResponseUpdate(BaseModel):
    action_status: Optional[str] = None  # OPEN | IN_PROGRESS | RESOLVED
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class ResponseResponse(BaseModel):
    id: int
    invoice_id: int
    response_type: str
    notes: Optional[str]
    assigned_to: Optional[str]
    action_status: str
    created_at: datetime
    updated_at: datetime

    # Joined
    invoice_no: Optional[str] = None
    client_name: Optional[str] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Dashboard Schemas
# ──────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_invoices: int
    total_overdue: int
    total_paid: int
    total_escalated: int
    total_amount_overdue: float
    total_amount_recovered: float
    recovery_rate: float  # percentage
    avg_days_outstanding: float
    follow_ups_sent_total: int


class StageDistribution(BaseModel):
    stage: int
    tone: str
    count: int


class RevenueTimeline(BaseModel):
    date: str
    amount: float
    cumulative: float
