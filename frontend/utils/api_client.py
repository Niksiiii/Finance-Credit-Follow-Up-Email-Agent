"""
HTTP API client for the Streamlit frontend.
Wraps all calls to the FastAPI backend.
"""

import requests
from typing import Optional

BASE_URL = "http://localhost:8000"


def _get(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to the backend."""
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is the API server running on port 8000?"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"API error: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


def _post(endpoint: str, json_data: dict = None, files: dict = None, params: dict = None) -> dict:
    """Make a POST request to the backend."""
    try:
        resp = requests.post(
            f"{BASE_URL}{endpoint}",
            json=json_data,
            files=files,
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is the API server running on port 8000?"}
    except requests.exceptions.HTTPError as e:
        try:
            return {"error": e.response.json()}
        except Exception:
            return {"error": f"API error: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


def _patch(endpoint: str, json_data: dict = None) -> dict:
    """Make a PATCH request to the backend."""
    try:
        resp = requests.patch(f"{BASE_URL}{endpoint}", json=json_data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is the API server running on port 8000?"}
    except Exception as e:
        return {"error": str(e)}


def _delete(endpoint: str) -> dict:
    """Make a DELETE request to the backend."""
    try:
        resp = requests.delete(f"{BASE_URL}{endpoint}", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ── Invoices ───────────────────────────────────────────────

def get_invoices(status: Optional[str] = None):
    params = {"status": status} if status else None
    return _get("/api/invoices", params=params)


def get_invoice(invoice_id: int):
    return _get(f"/api/invoices/{invoice_id}")


def update_invoice(invoice_id: int, data: dict):
    return _patch(f"/api/invoices/{invoice_id}", json_data=data)


def upload_file(file_content: bytes, filename: str):
    files = {"file": (filename, file_content)}
    return _post("/api/invoices/upload", files=files)


def clear_all_data():
    return _delete("/api/invoices/clear")


# ── Follow-Ups ─────────────────────────────────────────────

def trigger_followups(dry_run: bool = True):
    return _post("/api/followups/trigger", params={"dry_run": dry_run})


def start_automation(interval_hours: float = 24.0, dry_run: bool = True):
    return _post("/api/followups/automation/start", params={
        "interval_hours": interval_hours, "dry_run": dry_run
    })


def stop_automation():
    return _post("/api/followups/automation/stop")


def get_automation_status():
    return _get("/api/followups/automation/status")


def get_followup_logs(invoice_no: str = None, stage: int = None, send_status: str = None):
    params = {}
    if invoice_no:
        params["invoice_no"] = invoice_no
    if stage is not None:
        params["stage"] = stage
    if send_status:
        params["send_status"] = send_status
    return _get("/api/followups/logs", params=params)


def preview_email(invoice_id: int):
    return _get(f"/api/followups/preview/{invoice_id}")


# ── Dashboard ──────────────────────────────────────────────

def get_dashboard_stats():
    return _get("/api/dashboard/stats")


def get_stage_distribution():
    return _get("/api/dashboard/stage-distribution")


def get_revenue_timeline():
    return _get("/api/dashboard/revenue")


# ── Payments ───────────────────────────────────────────────

def record_payment(data: dict, dry_run: bool = True):
    return _post("/api/payments", json_data=data, params={"dry_run": dry_run})


def get_payments():
    return _get("/api/payments")


# ── Team ───────────────────────────────────────────────────

def get_team_members():
    return _get("/api/team")


def add_team_member(data: dict):
    return _post("/api/team", json_data=data)


def delete_team_member(member_id: int):
    return _delete(f"/api/team/{member_id}")


# ── Responses ──────────────────────────────────────────────

def get_responses(action_status: str = None, assigned_to: str = None):
    params = {}
    if action_status:
        params["action_status"] = action_status
    if assigned_to:
        params["assigned_to"] = assigned_to
    return _get("/api/responses", params=params)


def create_response(data: dict):
    return _post("/api/responses", json_data=data)


def update_response(response_id: int, data: dict):
    return _patch(f"/api/responses/{response_id}", json_data=data)


# ── Config ─────────────────────────────────────────────────

def get_config():
    return _get("/api/config")
