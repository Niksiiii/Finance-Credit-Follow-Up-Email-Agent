"""
SQLAlchemy ORM models for the Finance Credit Follow-Up Agent.
Tables: Invoice, FollowUpLog, Payment, TeamMember, ResponseTracker
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    Text, Boolean, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from .database import Base


class Invoice(Base):
    """Represents a pending credit / invoice record."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    client_name = Column(String(200), nullable=False)
    client_email = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    balance_amount = Column(Float, nullable=True)  # remaining balance after partial payment
    due_date = Column(Date, nullable=False)
    follow_up_count = Column(Integer, default=0)
    status = Column(
        String(20),
        default="PENDING",
        nullable=False,
    )  # PENDING | PAID | PARTIAL | ESCALATED | LEGAL_REVIEW
    assigned_to = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    follow_up_logs = relationship("FollowUpLog", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    responses = relationship("ResponseTracker", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_no} - {self.client_name}>"


class FollowUpLog(Base):
    """Audit log for every follow-up email generated/sent."""
    __tablename__ = "follow_up_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    stage = Column(Integer, nullable=False)  # 1-5
    tone = Column(String(50), nullable=False)  # Warm, Polite-Firm, Formal, Stern, Escalation Flag
    email_subject = Column(Text, nullable=False)
    email_body = Column(Text, nullable=False)
    send_status = Column(String(20), nullable=False)  # DRY_RUN | SENT | FAILED
    recipient_email = Column(String(200), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)

    # Relationship
    invoice = relationship("Invoice", back_populates="follow_up_logs")

    def __repr__(self):
        return f"<FollowUpLog stage={self.stage} status={self.send_status}>"


class Payment(Base):
    """Records payments received against invoices."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount_received = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_reference = Column(String(100), nullable=True)
    is_partial = Column(Boolean, default=False)
    balance_remaining = Column(Float, nullable=True)
    thank_you_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    invoice = relationship("Invoice", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.amount_received} for invoice_id={self.invoice_id}>"


class TeamMember(Base):
    """Finance team members who can be assigned escalated cases."""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    role = Column(String(50), nullable=False)  # Manager | Executive | Legal
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<TeamMember {self.name} ({self.role})>"


class ResponseTracker(Base):
    """Tracks client responses and finance team follow-up actions."""
    __tablename__ = "response_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    response_type = Column(
        String(30),
        nullable=False,
    )  # PROMISE_TO_PAY | DISPUTE | PARTIAL_PAYMENT | NO_RESPONSE
    notes = Column(Text, nullable=True)
    assigned_to = Column(String(200), nullable=True)
    action_status = Column(
        String(20),
        default="OPEN",
        nullable=False,
    )  # OPEN | IN_PROGRESS | RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    invoice = relationship("Invoice", back_populates="responses")

    def __repr__(self):
        return f"<ResponseTracker type={self.response_type} status={self.action_status}>"
