"""
Data ingestion service.
Parses CSV/Excel files and upserts invoice records into the database.
"""

import logging
from typing import Tuple, List
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from ..models import Invoice

logger = logging.getLogger(__name__)

# Required columns in the uploaded file
REQUIRED_COLUMNS = {
    "invoice_no",
    "client_name",
    "client_email",
    "amount",
    "due_date",
}

# Column name aliases (common variations mapped to canonical names)
COLUMN_ALIASES = {
    "invoice_number": "invoice_no",
    "invoice_num": "invoice_no",
    "invoice no": "invoice_no",
    "invoice #": "invoice_no",
    "client": "client_name",
    "customer_name": "client_name",
    "customer": "client_name",
    "email": "client_email",
    "contact_email": "client_email",
    "customer_email": "client_email",
    "amount_due": "amount",
    "total_amount": "amount",
    "invoice_amount": "amount",
    "due": "due_date",
    "payment_due_date": "due_date",
    "followup_count": "follow_up_count",
    "follow_up_count": "follow_up_count",
    "reminders_sent": "follow_up_count",
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names using aliases."""
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.rename(columns=COLUMN_ALIASES)
    return df


def _validate_dataframe(df: pd.DataFrame) -> List[str]:
    """Validate that all required columns are present. Returns list of errors."""
    errors = []
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
    return errors


def parse_file(file_content: bytes, filename: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse a CSV or Excel file into a DataFrame.
    
    Returns:
        Tuple of (DataFrame, list of error messages).
        If errors is non-empty, the DataFrame may be empty.
    """
    errors = []

    try:
        if filename.endswith(".csv"):
            import io
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith((".xlsx", ".xls")):
            import io
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            return pd.DataFrame(), [f"Unsupported file format: {filename}. Use CSV or Excel."]
    except Exception as e:
        return pd.DataFrame(), [f"Failed to parse file: {e}"]

    if df.empty:
        return df, ["File is empty."]

    # Normalise columns
    df = _normalise_columns(df)

    # Validate
    errors = _validate_dataframe(df)
    if errors:
        return df, errors

    # Parse due_date
    try:
        df["due_date"] = pd.to_datetime(df["due_date"], format="mixed", dayfirst=False).dt.date
    except Exception as e:
        errors.append(f"Failed to parse due_date column: {e}")
        return df, errors

    # Set defaults for optional columns
    if "follow_up_count" not in df.columns:
        df["follow_up_count"] = 0
    if "status" not in df.columns:
        df["status"] = "PENDING"

    # Clean up amount
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if df["amount"].isna().any():
        errors.append("Some rows have invalid amount values.")

    # Drop rows with NaN in required fields
    df = df.dropna(subset=list(REQUIRED_COLUMNS))

    return df, errors


def ingest_dataframe(db: Session, df: pd.DataFrame) -> Tuple[int, int, List[str]]:
    """
    Upsert invoice records from a DataFrame into the database.
    Skips duplicates (by invoice_no).
    
    Returns:
        Tuple of (inserted_count, skipped_count, errors).
    """
    inserted = 0
    skipped = 0
    errors = []

    for _, row in df.iterrows():
        try:
            # Check for existing invoice
            existing = db.query(Invoice).filter(
                Invoice.invoice_no == str(row["invoice_no"])
            ).first()

            if existing:
                skipped += 1
                continue

            invoice = Invoice(
                invoice_no=str(row["invoice_no"]),
                client_name=str(row["client_name"]),
                client_email=str(row["client_email"]),
                amount=float(row["amount"]),
                due_date=row["due_date"],
                follow_up_count=int(row.get("follow_up_count", 0)),
                status=str(row.get("status", "PENDING")),
            )
            db.add(invoice)
            inserted += 1

        except Exception as e:
            errors.append(f"Row {row.get('invoice_no', '?')}: {e}")

    db.commit()
    logger.info(f"Data ingestion complete: {inserted} inserted, {skipped} skipped, {len(errors)} errors")
    return inserted, skipped, errors
