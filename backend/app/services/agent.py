"""
Follow-Up Agent Orchestrator.
Core engine that identifies overdue invoices, generates emails, sends/logs them,
and handles escalation and payment thank-you flows.
"""

import logging
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Invoice, FollowUpLog, Payment
from ..config import get_settings
from .tone_engine import get_tone_config, get_stage_from_days
from .email_generator import (
    generate_follow_up_email,
    generate_thank_you_email,
    generate_fallback_follow_up_email,
    EmailOutput,
)
from .email_sender import send_email, SendResult
from ..utils.security import mask_email

logger = logging.getLogger(__name__)
settings = get_settings()


def _calculate_days_overdue(due_date: date) -> int:
    """Calculate the number of days an invoice is overdue."""
    delta = date.today() - due_date
    return max(0, delta.days)


def _get_payment_link(invoice_no: str) -> str:
    """Generate a dynamic payment link for the invoice."""
    return f"{settings.PAYMENT_LINK_BASE}/{invoice_no}"


def get_overdue_invoices(db: Session) -> List[Invoice]:
    """Fetch all overdue, pending invoices."""
    today = date.today()
    return db.query(Invoice).filter(
        Invoice.status == "PENDING",
        Invoice.due_date < today,
    ).order_by(Invoice.due_date.asc()).all()


def preview_email_for_invoice(db: Session, invoice_id: int) -> Optional[dict]:
    """
    Generate a preview of the follow-up email for a specific invoice.
    Does NOT send or log — purely for preview purposes.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return None

    days_overdue = _calculate_days_overdue(invoice.due_date)
    tone_config = get_tone_config(days_overdue)

    if not tone_config:
        return {"message": "Invoice is not overdue."}

    if tone_config.is_escalation_flag:
        return {
            "invoice_no": invoice.invoice_no,
            "client_name": invoice.client_name,
            "stage": 5,
            "tone": "Escalation Flag",
            "subject": "⚠️ ESCALATED — Requires manual legal/finance review",
            "body": f"Invoice #{invoice.invoice_no} for ₹{invoice.amount:,.2f} is {days_overdue} days overdue. This has been flagged for manual review by the finance/legal team.",
            "days_overdue": days_overdue,
        }

    payment_link = _get_payment_link(invoice.invoice_no)

    try:
        email = generate_follow_up_email(
            client_name=invoice.client_name,
            invoice_no=invoice.invoice_no,
            amount=invoice.amount,
            due_date=invoice.due_date.strftime("%d %b %Y"),
            days_overdue=days_overdue,
            tone_config=tone_config,
            payment_link=payment_link,
        )
    except Exception as e:
        logger.warning(f"LLM failed, using fallback: {e}")
        email = generate_fallback_follow_up_email(
            client_name=invoice.client_name,
            invoice_no=invoice.invoice_no,
            amount=invoice.amount,
            due_date=invoice.due_date.strftime("%d %b %Y"),
            days_overdue=days_overdue,
            tone_config=tone_config,
            payment_link=payment_link,
        )

    return {
        "invoice_no": invoice.invoice_no,
        "client_name": invoice.client_name,
        "stage": tone_config.stage,
        "tone": tone_config.tone_label,
        "subject": email.subject,
        "body": email.body,
        "days_overdue": days_overdue,
    }


def process_single_invoice(
    db: Session,
    invoice: Invoice,
    dry_run: bool = True,
) -> dict:
    """
    Process a single overdue invoice:
    1. Determine stage & tone
    2. Generate email (LLM or fallback)
    3. Send or dry-run
    4. Log to audit trail
    5. Update invoice follow-up count
    """
    days_overdue = _calculate_days_overdue(invoice.due_date)
    tone_config = get_tone_config(days_overdue)
    result = {
        "invoice_no": invoice.invoice_no,
        "client_name": invoice.client_name,
        "days_overdue": days_overdue,
    }

    if not tone_config:
        result["action"] = "SKIPPED"
        result["reason"] = "Not overdue"
        return result

    # ── Stage 5: Escalation Flag ──
    if tone_config.is_escalation_flag:
        invoice.status = "LEGAL_REVIEW"
        invoice.updated_at = datetime.utcnow()

        # Log the escalation
        log_entry = FollowUpLog(
            invoice_id=invoice.id,
            stage=5,
            tone="Escalation Flag",
            email_subject="ESCALATED — Flagged for Legal/Finance Review",
            email_body=f"Invoice #{invoice.invoice_no} (₹{invoice.amount:,.2f}) is {days_overdue} days overdue. Auto-escalated to legal/finance team for manual review.",
            send_status="ESCALATED",
            recipient_email=invoice.client_email,
        )
        db.add(log_entry)
        db.commit()

        result["action"] = "ESCALATED"
        result["stage"] = 5
        result["tone"] = "Escalation Flag"
        logger.info(f"[ESCALATED] {invoice.invoice_no} → legal review ({days_overdue} days overdue)")
        return result

    # ── Stages 1-4: Generate & Send Email ──
    payment_link = _get_payment_link(invoice.invoice_no)

    try:
        email = generate_follow_up_email(
            client_name=invoice.client_name,
            invoice_no=invoice.invoice_no,
            amount=invoice.amount,
            due_date=invoice.due_date.strftime("%d %b %Y"),
            days_overdue=days_overdue,
            tone_config=tone_config,
            payment_link=payment_link,
        )
    except Exception as e:
        logger.warning(f"LLM failed for {invoice.invoice_no}, using fallback: {e}")
        email = generate_fallback_follow_up_email(
            client_name=invoice.client_name,
            invoice_no=invoice.invoice_no,
            amount=invoice.amount,
            due_date=invoice.due_date.strftime("%d %b %Y"),
            days_overdue=days_overdue,
            tone_config=tone_config,
            payment_link=payment_link,
        )

    # Send or dry-run
    send_result = send_email(
        to_email=invoice.client_email,
        subject=email.subject,
        body=email.body,
        dry_run=dry_run,
    )

    # Log to audit trail
    log_entry = FollowUpLog(
        invoice_id=invoice.id,
        stage=tone_config.stage,
        tone=tone_config.tone_label,
        email_subject=email.subject,
        email_body=email.body,
        send_status=send_result.status,
        recipient_email=invoice.client_email,
        error_message=send_result.error_message if send_result.error_message else None,
    )
    db.add(log_entry)

    # Update invoice
    invoice.follow_up_count += 1
    if tone_config.stage == 4:
        invoice.status = "ESCALATED"
    invoice.updated_at = datetime.utcnow()

    db.commit()

    result["action"] = send_result.status
    result["stage"] = tone_config.stage
    result["tone"] = tone_config.tone_label
    result["subject"] = email.subject
    result["email_to"] = mask_email(invoice.client_email)

    logger.info(
        f"[{send_result.status}] {invoice.invoice_no} → Stage {tone_config.stage} "
        f"({tone_config.tone_label}) to {mask_email(invoice.client_email)}"
    )

    return result


def run_follow_up_agent(db: Session, dry_run: bool = True) -> dict:
    """
    Main agent entry point.
    Scans all overdue invoices and dispatches appropriate follow-ups.
    
    Returns a summary of actions taken.
    """
    logger.info(f"{'='*60}")
    logger.info(f"Follow-Up Agent Started | Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    logger.info(f"{'='*60}")

    overdue_invoices = get_overdue_invoices(db)
    logger.info(f"Found {len(overdue_invoices)} overdue invoices")

    results = {
        "total_processed": 0,
        "emails_sent": 0,
        "emails_dry_run": 0,
        "emails_failed": 0,
        "escalated_to_legal": 0,
        "details": [],
    }

    for invoice in overdue_invoices:
        detail = process_single_invoice(db, invoice, dry_run=dry_run)
        results["details"].append(detail)
        results["total_processed"] += 1

        action = detail.get("action", "")
        if action == "SENT":
            results["emails_sent"] += 1
        elif action == "DRY_RUN":
            results["emails_dry_run"] += 1
        elif action == "FAILED":
            results["emails_failed"] += 1
        elif action == "ESCALATED":
            results["escalated_to_legal"] += 1

    logger.info(f"{'='*60}")
    logger.info(f"Agent Complete | Processed: {results['total_processed']} | "
                f"Sent: {results['emails_sent']} | Dry-Run: {results['emails_dry_run']} | "
                f"Failed: {results['emails_failed']} | Escalated: {results['escalated_to_legal']}")
    logger.info(f"{'='*60}")

    return results


def process_payment_and_thank(
    db: Session,
    payment: Payment,
    invoice: Invoice,
    dry_run: bool = True,
) -> dict:
    """
    Process a recorded payment: handle full or partial payment.
    - Full payment: mark PAID, send thank-you
    - Partial payment: mark PARTIAL, send thank-you with balance info
    """
    # Calculate total paid so far (including this payment)
    from sqlalchemy import func
    total_paid = db.query(func.coalesce(func.sum(Payment.amount_received), 0)).filter(
        Payment.invoice_id == invoice.id
    ).scalar() or 0

    balance = invoice.amount - total_paid
    is_partial = balance > 0.01  # small tolerance for floating point

    # Update payment record
    payment.is_partial = is_partial
    payment.balance_remaining = max(0, round(balance, 2)) if is_partial else 0

    # Update invoice
    if is_partial:
        invoice.status = "PARTIAL"
        invoice.balance_amount = round(balance, 2)
        # If 50%+ paid, reduce follow_up_count by 1 → lowers escalation stage
        paid_ratio = total_paid / invoice.amount if invoice.amount > 0 else 0
        if paid_ratio >= 0.5 and invoice.follow_up_count > 0:
            invoice.follow_up_count = max(0, invoice.follow_up_count - 1)
            logger.info(f"[STAGE REDUCED] {invoice.invoice_no} — {paid_ratio*100:.0f}% paid, follow-up count reduced to {invoice.follow_up_count}")
    else:
        invoice.status = "PAID"
        invoice.balance_amount = 0
    invoice.updated_at = datetime.utcnow()

    # Generate appropriate email
    payment_link = _get_payment_link(invoice.invoice_no)

    if is_partial:
        # Partial payment — thank you + balance info
        try:
            from .email_generator import generate_partial_payment_email
            email = generate_partial_payment_email(
                client_name=invoice.client_name,
                invoice_no=invoice.invoice_no,
                amount_paid=payment.amount_received,
                original_amount=invoice.amount,
                balance_remaining=balance,
                payment_date=payment.payment_date.strftime("%d %b %Y"),
                payment_reference=payment.payment_reference or "N/A",
                payment_link=payment_link,
            )
        except Exception as e:
            logger.warning(f"LLM failed for partial payment email: {e}")
            email = EmailOutput(
                subject=f"Thank You – Balance of ₹{balance:,.2f} Pending | Invoice #{invoice.invoice_no}",
                body=f"Dear {invoice.client_name},\n\nThank you for your payment of ₹{payment.amount_received:,.2f} "
                     f"towards Invoice #{invoice.invoice_no} (₹{invoice.amount:,.2f}).\n\n"
                     f"A balance of ₹{balance:,.2f} remains outstanding. Please clear it at your earliest convenience.\n\n"
                     f"Payment Link: {payment_link}\n\n"
                     f"Best regards,\nFinance Team",
            )
        tone_label = "Partial Payment Thank You"
    else:
        # Full payment — standard thank you
        try:
            email = generate_thank_you_email(
                client_name=invoice.client_name,
                invoice_no=invoice.invoice_no,
                amount_paid=payment.amount_received,
                original_amount=invoice.amount,
                payment_date=payment.payment_date.strftime("%d %b %Y"),
                payment_reference=payment.payment_reference or "N/A",
            )
        except Exception as e:
            logger.warning(f"LLM failed for thank-you email: {e}")
            email = EmailOutput(
                subject=f"Thank You – Payment Received for Invoice #{invoice.invoice_no}",
                body=f"Dear {invoice.client_name},\n\nThank you for your payment of ₹{payment.amount_received:,.2f} "
                     f"for Invoice #{invoice.invoice_no}. Your account is now in good standing.\n\n"
                     f"Best regards,\nFinance Team",
            )
        tone_label = "Thank You"

    # Send email
    send_result = send_email(
        to_email=invoice.client_email,
        subject=email.subject,
        body=email.body,
        dry_run=dry_run,
    )

    # Log it
    log_entry = FollowUpLog(
        invoice_id=invoice.id,
        stage=0,  # 0 = thank you / partial thank you
        tone=tone_label,
        email_subject=email.subject,
        email_body=email.body,
        send_status=send_result.status,
        recipient_email=invoice.client_email,
        error_message=send_result.error_message if send_result.error_message else None,
    )
    db.add(log_entry)

    payment.thank_you_sent = True
    db.commit()

    logger.info(f"[{tone_label.upper()} {send_result.status}] {invoice.invoice_no} → {mask_email(invoice.client_email)}"
                + (f" | Balance: ₹{balance:,.2f}" if is_partial else ""))

    return {
        "invoice_no": invoice.invoice_no,
        "thank_you_status": send_result.status,
        "subject": email.subject,
        "is_partial": is_partial,
        "balance_remaining": round(balance, 2) if is_partial else 0,
    }

