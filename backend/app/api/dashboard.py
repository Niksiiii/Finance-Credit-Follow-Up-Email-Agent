"""
Dashboard API endpoints.
KPIs, revenue timeline, stage distribution.
"""

from datetime import date
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Invoice, FollowUpLog, Payment
from ..schemas import DashboardStats, StageDistribution, RevenueTimeline
from ..services.tone_engine import get_stage_from_days, ESCALATION_MATRIX

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get high-level KPI statistics."""
    today = date.today()

    total_invoices = db.query(Invoice).count()

    # Include PARTIAL in overdue count
    total_overdue = db.query(Invoice).filter(
        Invoice.status.in_(["PENDING", "PARTIAL"]),
        Invoice.due_date < today,
    ).count()

    total_paid = db.query(Invoice).filter(Invoice.status == "PAID").count()

    total_escalated = db.query(Invoice).filter(
        Invoice.status.in_(["ESCALATED", "LEGAL_REVIEW"])
    ).count()

    # Use balance_amount where available, otherwise full amount
    overdue_invoices_for_amount = db.query(Invoice).filter(
        Invoice.status.in_(["PENDING", "PARTIAL"]),
        Invoice.due_date < today,
    ).all()

    total_amount_overdue = sum(
        (inv.balance_amount if inv.balance_amount is not None else inv.amount)
        for inv in overdue_invoices_for_amount
    )

    total_amount_recovered = db.query(
        func.coalesce(func.sum(Payment.amount_received), 0)
    ).scalar() or 0

    # Recovery rate
    total_amount_all = db.query(func.coalesce(func.sum(Invoice.amount), 0)).scalar() or 0
    recovery_rate = (total_amount_recovered / total_amount_all * 100) if total_amount_all > 0 else 0

    # Average days outstanding for overdue invoices
    overdue_for_dso = db.query(Invoice).filter(
        Invoice.status.in_(["PENDING", "PARTIAL"]),
        Invoice.due_date < today,
    ).all()
    if overdue_for_dso:
        total_days = sum((today - inv.due_date).days for inv in overdue_for_dso)
        avg_dso = total_days / len(overdue_for_dso)
    else:
        avg_dso = 0

    follow_ups_total = db.query(FollowUpLog).count()

    return DashboardStats(
        total_invoices=total_invoices,
        total_overdue=total_overdue,
        total_paid=total_paid,
        total_escalated=total_escalated,
        total_amount_overdue=round(total_amount_overdue, 2),
        total_amount_recovered=round(total_amount_recovered, 2),
        recovery_rate=round(recovery_rate, 1),
        avg_days_outstanding=round(avg_dso, 1),
        follow_ups_sent_total=follow_ups_total,
    )


@router.get("/stage-distribution", response_model=List[StageDistribution])
def get_stage_distribution(db: Session = Depends(get_db)):
    """Get the distribution of overdue invoices across escalation stages."""
    today = date.today()
    overdue_invoices = db.query(Invoice).filter(
        Invoice.status.in_(["PENDING", "PARTIAL", "ESCALATED", "LEGAL_REVIEW"]),
        Invoice.due_date < today,
    ).all()

    # Count invoices per stage (with partial payment stage reduction)
    stage_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for inv in overdue_invoices:
        days = (today - inv.due_date).days
        stage = get_stage_from_days(days)

        # Reduce stage by 1 if 50%+ paid
        if inv.status == "PARTIAL" and inv.balance_amount is not None and stage > 0:
            paid_ratio = 1 - (inv.balance_amount / inv.amount) if inv.amount > 0 else 0
            if paid_ratio >= 0.5:
                stage = max(1, stage - 1)

        if stage in stage_counts:
            stage_counts[stage] += 1

    result = []
    for stage, count in stage_counts.items():
        tone_config = ESCALATION_MATRIX.get(stage)
        result.append(StageDistribution(
            stage=stage,
            tone=tone_config.tone_label if tone_config else "Unknown",
            count=count,
        ))

    return result


@router.get("/revenue", response_model=List[RevenueTimeline])
def get_revenue_timeline(db: Session = Depends(get_db)):
    """Get revenue recovered over time for charting."""
    payments = db.query(Payment).order_by(Payment.payment_date.asc()).all()

    timeline = {}
    cumulative = 0
    for payment in payments:
        date_str = payment.payment_date.strftime("%Y-%m-%d")
        if date_str not in timeline:
            timeline[date_str] = 0
        timeline[date_str] += payment.amount_received

    result = []
    cumulative = 0
    for date_str, amount in sorted(timeline.items()):
        cumulative += amount
        result.append(RevenueTimeline(
            date=date_str,
            amount=round(amount, 2),
            cumulative=round(cumulative, 2),
        ))

    return result
