"""
LLM-powered email generation using LangChain + Google Gemini.
Generates personalised follow-up emails and thank-you emails.
Uses SQLite cache to reduce API costs during development.
"""

import os
from dataclasses import dataclass
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache
from ..config import get_settings
from .tone_engine import ToneConfig

settings = get_settings()

# ── LLM Cache Setup ─────────────────────────────────────────
cache_path = os.path.join(os.path.dirname(settings.DB_PATH), ".langchain_cache.db")
set_llm_cache(SQLiteCache(database_path=cache_path))


@dataclass
class EmailOutput:
    """Generated email output."""
    subject: str
    body: str


def _get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Create a Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        max_output_tokens=1024,
    )


# ── Follow-Up Email Prompt ──────────────────────────────────

FOLLOW_UP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional finance communication specialist. 
Generate a follow-up email for an overdue invoice payment.

RULES:
- Tone: {tone_label}
- Key message: {key_message_hint}
- Call to action: {cta_hint}
- You MUST include ALL of these details in the email: client name, invoice number, amount due, due date, days overdue, and payment link.
- Do NOT generate a generic email. Every field must be populated from the provided data.
- Use Indian Rupee symbol (₹) for currency.
- Be professional and maintain business relationships.
- For Stage 1-2: Use first name. For Stage 3-4: Use Mr./Ms. with last name.
- Keep the email concise but complete.

OUTPUT FORMAT:
Return ONLY the email in this exact format:
SUBJECT: [email subject line]
BODY: [complete email body]"""),
    ("human", """Generate a follow-up email with these details:

Client Name: {client_name}
Invoice Number: {invoice_no}
Amount Due: ₹{amount}
Due Date: {due_date}
Days Overdue: {days_overdue}
Payment Link: {payment_link}
Follow-Up Stage: {stage} ({tone_label})
Contact Email: finance@yourcompany.com
Contact Phone: +91-11-4000-1234"""),
])


# ── Thank You Email Prompt ──────────────────────────────────

THANK_YOU_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional finance communication specialist.
Generate a warm thank-you email for a received payment.

RULES:
- Be warm, grateful, and professional.
- Include all payment details.
- Use Indian Rupee symbol (₹) for currency.
- Keep it brief and positive.
- Mention that their account is now in good standing.

OUTPUT FORMAT:
Return ONLY the email in this exact format:
SUBJECT: [email subject line]
BODY: [complete email body]"""),
    ("human", """Generate a thank-you email with these details:

Client Name: {client_name}
Invoice Number: {invoice_no}
Amount Paid: ₹{amount_paid}
Original Amount: ₹{original_amount}
Payment Date: {payment_date}
Payment Reference: {payment_reference}"""),
])


def _parse_email_output(raw_text: str) -> EmailOutput:
    """Parse the LLM output into subject and body."""
    lines = raw_text.strip().split("\n")
    subject = ""
    body_lines = []
    in_body = False

    for line in lines:
        if line.upper().startswith("SUBJECT:"):
            subject = line.split(":", 1)[1].strip()
        elif line.upper().startswith("BODY:"):
            in_body = True
            rest = line.split(":", 1)[1].strip()
            if rest:
                body_lines.append(rest)
        elif in_body:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # Fallback if parsing fails
    if not subject:
        subject = f"Payment Follow-Up Reminder"
    if not body:
        body = raw_text

    return EmailOutput(subject=subject, body=body)


def generate_follow_up_email(
    client_name: str,
    invoice_no: str,
    amount: float,
    due_date: str,
    days_overdue: int,
    tone_config: ToneConfig,
    payment_link: str,
) -> EmailOutput:
    """
    Generate a personalised follow-up email using the LLM.
    All fields are injected from the data source — no generic emails.
    """
    llm = _get_llm(temperature=tone_config.temperature)
    chain = FOLLOW_UP_PROMPT | llm

    response = chain.invoke({
        "client_name": client_name,
        "invoice_no": invoice_no,
        "amount": f"{amount:,.2f}",
        "due_date": due_date,
        "days_overdue": days_overdue,
        "payment_link": payment_link,
        "stage": tone_config.stage,
        "tone_label": tone_config.tone_label,
        "key_message_hint": tone_config.key_message_hint,
        "cta_hint": tone_config.cta_hint,
    })

    return _parse_email_output(response.content)


def generate_thank_you_email(
    client_name: str,
    invoice_no: str,
    amount_paid: float,
    original_amount: float,
    payment_date: str,
    payment_reference: str = "N/A",
) -> EmailOutput:
    """Generate a thank-you email for a received payment."""
    llm = _get_llm(temperature=0.4)
    chain = THANK_YOU_PROMPT | llm

    response = chain.invoke({
        "client_name": client_name,
        "invoice_no": invoice_no,
        "amount_paid": f"{amount_paid:,.2f}",
        "original_amount": f"{original_amount:,.2f}",
        "payment_date": payment_date,
        "payment_reference": payment_reference,
    })

    return _parse_email_output(response.content)


def generate_fallback_follow_up_email(
    client_name: str,
    invoice_no: str,
    amount: float,
    due_date: str,
    days_overdue: int,
    tone_config: ToneConfig,
    payment_link: str,
) -> EmailOutput:
    """
    Fallback email generator when LLM is unavailable.
    Uses template-based generation without any API calls.
    """
    first_name = client_name.split()[0] if client_name else "Client"
    formal_name = f"Mr./Ms. {client_name.split()[-1]}" if client_name else "Client"

    templates = {
        1: {
            "subject": f"Quick Reminder – Invoice #{invoice_no} | ₹{amount:,.2f} Due",
            "body": f"""Hi {first_name},

I hope you're doing well! This is a friendly reminder that Invoice #{invoice_no} for ₹{amount:,.2f} was due on {due_date}.

If you have already processed this payment, please disregard this message. Otherwise, you can make the payment using the link below:

Payment Link: {payment_link}

Thank you for your prompt attention to this matter!

Best regards,
Finance Team
Contact: finance@yourcompany.com | +91-11-4000-1234"""
        },
        2: {
            "subject": f"Payment Reminder – Invoice #{invoice_no} | ₹{amount:,.2f} ({days_overdue} Days Overdue)",
            "body": f"""Hi {first_name},

We hope this message finds you well. We are writing to follow up on Invoice #{invoice_no} for ₹{amount:,.2f}, which was due on {due_date} and is now {days_overdue} days overdue.

We understand that oversights happen, and we would appreciate it if you could confirm a payment date at your earliest convenience.

Payment Link: {payment_link}

If you have any questions about this invoice, please don't hesitate to reach out.

Kind regards,
Finance Team
Contact: finance@yourcompany.com | +91-11-4000-1234"""
        },
        3: {
            "subject": f"IMPORTANT: Outstanding Payment – Invoice #{invoice_no} ({days_overdue} Days Overdue)",
            "body": f"""Dear {formal_name},

Despite our previous reminders, Invoice #{invoice_no} for ₹{amount:,.2f} remains unpaid as of today, now {days_overdue} days overdue (original due date: {due_date}).

We request your immediate attention to this matter. Continued non-payment may impact your credit terms with our organization.

Please respond within 48 hours with a confirmed payment date or contact us to discuss any concerns.

Payment Link: {payment_link}

Regards,
Finance Team
Contact: finance@yourcompany.com | +91-11-4000-1234"""
        },
        4: {
            "subject": f"FINAL NOTICE – Invoice #{invoice_no} – Immediate Action Required",
            "body": f"""Dear {formal_name},

This is our FINAL reminder regarding Invoice #{invoice_no} for ₹{amount:,.2f}, which is now {days_overdue} days overdue (original due date: {due_date}).

Failure to remit payment within 24 hours will result in escalation to our legal and recovery team. This may affect your credit standing and business relationship with us.

Please act immediately:
Payment Link: {payment_link}
Or call us: +91-11-4000-1234

Regards,
Finance & Collections Team
Contact: finance@yourcompany.com"""
        },
    }

    template = templates.get(tone_config.stage, templates[1])
    return EmailOutput(subject=template["subject"], body=template["body"])


# ── Partial Payment Thank You Prompt ─────────────────────

PARTIAL_PAYMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional finance communication specialist.
Generate a thank-you email for a PARTIAL payment received. The client has paid less than the full amount.

RULES:
- Be warm and grateful for the payment received.
- Clearly mention the balance amount still outstanding.
- Include a polite request to clear the balance.
- Use Indian Rupee symbol (₹) for currency.
- Include the payment link for the remaining balance.
- Keep it professional and positive.

OUTPUT FORMAT:
Return ONLY the email in this exact format:
SUBJECT: [email subject line]
BODY: [complete email body]"""),
    ("human", """Generate a partial payment thank-you email with these details:

Client Name: {client_name}
Invoice Number: {invoice_no}
Amount Paid: ₹{amount_paid}
Original Amount: ₹{original_amount}
Balance Remaining: ₹{balance_remaining}
Payment Date: {payment_date}
Payment Reference: {payment_reference}
Payment Link: {payment_link}"""),
])


def generate_partial_payment_email(
    client_name: str,
    invoice_no: str,
    amount_paid: float,
    original_amount: float,
    balance_remaining: float,
    payment_date: str,
    payment_reference: str = "N/A",
    payment_link: str = "",
) -> EmailOutput:
    """Generate a thank-you email for partial payment with balance info."""
    try:
        llm = _get_llm(temperature=0.4)
        chain = PARTIAL_PAYMENT_PROMPT | llm

        response = chain.invoke({
            "client_name": client_name,
            "invoice_no": invoice_no,
            "amount_paid": f"{amount_paid:,.2f}",
            "original_amount": f"{original_amount:,.2f}",
            "balance_remaining": f"{balance_remaining:,.2f}",
            "payment_date": payment_date,
            "payment_reference": payment_reference,
            "payment_link": payment_link,
        })

        return _parse_email_output(response.content)
    except Exception:
        # Fallback template
        first_name = client_name.split()[0] if client_name else "Client"
        return EmailOutput(
            subject=f"Thank You for Your Payment – Balance of ₹{balance_remaining:,.2f} Pending | Invoice #{invoice_no}",
            body=f"""Dear {first_name},

Thank you for your payment of ₹{amount_paid:,.2f} towards Invoice #{invoice_no} (original amount: ₹{original_amount:,.2f}), received on {payment_date}.

We appreciate your prompt action. However, please note that a balance of ₹{balance_remaining:,.2f} remains outstanding on this invoice.

We kindly request you to clear the remaining balance at your earliest convenience using the link below:

Payment Link: {payment_link}
Payment Reference: {payment_reference}

If you have any questions or concerns, please don't hesitate to reach out.

Best regards,
Finance Team
Contact: finance@yourcompany.com | +91-11-4000-1234"""
        )

