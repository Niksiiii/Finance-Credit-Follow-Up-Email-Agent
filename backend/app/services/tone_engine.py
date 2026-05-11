"""
Tone Escalation Engine.
Maps days overdue → stage → tone configuration.
Implements the escalation matrix from the business requirements.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToneConfig:
    """Configuration for a follow-up email tone."""
    stage: int
    tone_label: str
    key_message_hint: str
    cta_hint: str
    is_escalation_flag: bool = False
    temperature: float = 0.3


# ── Escalation Matrix ──────────────────────────────────────────

ESCALATION_MATRIX = {
    1: ToneConfig(
        stage=1,
        tone_label="Warm & Friendly",
        key_message_hint="Gentle reminder, assume oversight. Be warm and courteous.",
        cta_hint="Pay now link / bank details",
        temperature=0.3,
    ),
    2: ToneConfig(
        stage=2,
        tone_label="Polite but Firm",
        key_message_hint="Payment still pending; politely request confirmation of payment date.",
        cta_hint="Confirm payment date",
        temperature=0.3,
    ),
    3: ToneConfig(
        stage=3,
        tone_label="Formal & Serious",
        key_message_hint="Escalating concern; mention potential impact on credit terms. Professional and serious.",
        cta_hint="Respond within 48 hours",
        temperature=0.1,
    ),
    4: ToneConfig(
        stage=4,
        tone_label="Stern & Urgent",
        key_message_hint="Final reminder before legal escalation. Urgent and direct. Mention consequences.",
        cta_hint="Pay immediately or call us",
        temperature=0.1,
    ),
    5: ToneConfig(
        stage=5,
        tone_label="Escalation Flag",
        key_message_hint="Human review required; no auto email to be sent.",
        cta_hint="Assign to finance manager",
        is_escalation_flag=True,
        temperature=0.0,
    ),
}


def get_stage_from_days(days_overdue: int) -> int:
    """Determine the follow-up stage based on days overdue."""
    if days_overdue <= 0:
        return 0  # Not overdue
    elif days_overdue <= 7:
        return 1
    elif days_overdue <= 14:
        return 2
    elif days_overdue <= 21:
        return 3
    elif days_overdue <= 30:
        return 4
    else:
        return 5  # Escalation flag


def get_tone_config(days_overdue: int) -> Optional[ToneConfig]:
    """
    Get the tone configuration for a given number of days overdue.
    Returns None if the invoice is not overdue.
    """
    stage = get_stage_from_days(days_overdue)
    if stage == 0:
        return None
    return ESCALATION_MATRIX.get(stage)


def get_tone_config_by_stage(stage: int) -> Optional[ToneConfig]:
    """Get tone config directly by stage number."""
    return ESCALATION_MATRIX.get(stage)
