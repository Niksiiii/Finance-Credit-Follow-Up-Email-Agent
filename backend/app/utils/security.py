"""
Input sanitisation and PII masking utilities.
"""

import re
import html
import logging

logger = logging.getLogger(__name__)


def sanitise_input(text: str) -> str:
    """
    Sanitise user input to prevent prompt injection and XSS.
    - Strips HTML tags
    - Escapes special characters
    - Removes potential prompt injection patterns
    """
    if not text:
        return text

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Escape HTML entities
    text = html.escape(text)

    # Remove common prompt injection patterns
    injection_patterns = [
        r"ignore\s+(previous|above|all)\s+instructions",
        r"disregard\s+(previous|above|all)",
        r"forget\s+(everything|all|previous)",
        r"new\s+instructions?\s*:",
        r"system\s*prompt\s*:",
        r"you\s+are\s+now",
        r"act\s+as\s+(if|a|an)",
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

    return text.strip()


def mask_email(email: str) -> str:
    """
    Mask an email address for logging purposes.
    e.g., 'rajesh.kapoor@company.com' → 'r*****r@c****y.com'
    """
    if not email or "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    domain_parts = domain.split(".")

    # Mask local part
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    # Mask domain name (keep TLD)
    if len(domain_parts) >= 2:
        name = domain_parts[0]
        if len(name) <= 2:
            masked_name = name[0] + "*"
        else:
            masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
        masked_domain = masked_name + "." + ".".join(domain_parts[1:])
    else:
        masked_domain = domain

    return f"{masked_local}@{masked_domain}"


def mask_amount(amount: float) -> str:
    """Mask currency amount for logging — keep magnitude only."""
    if amount < 1000:
        return "₹***"
    elif amount < 100000:
        return f"₹**,***"
    else:
        return f"₹*,**,***"


def validate_invoice_no(invoice_no: str) -> bool:
    """Validate invoice number format."""
    if not invoice_no:
        return False
    # Allow alphanumeric with hyphens and underscores
    return bool(re.match(r"^[A-Za-z0-9\-_]+$", invoice_no))


def validate_email_format(email: str) -> bool:
    """Basic email format validation."""
    if not email:
        return False
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))
