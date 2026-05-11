"""
📂 Upload — CSV/Excel file upload with preview and validation.
"""

import streamlit as st
import pandas as pd
import requests
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import get_invoices, clear_all_data
from utils.theme import BANKING_THEME, page_header, sidebar_branding

BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent — Upload", page_icon="📂", layout="wide")
st.markdown(BANKING_THEME, unsafe_allow_html=True)
sidebar_branding()
page_header("📂", "Upload Invoice Data", "Import your pending credit records from CSV or Excel files")

st.markdown("""
<style>
.upload-zone { background: #FFFFFF; border: 2px dashed #CBD5E1;
    border-radius: 16px; padding: 2rem; text-align: center; margin: 1rem 0; }
.upload-zone:hover { border-color: #1D4ED8; }
.upload-icon { font-size: 3rem; }
.upload-text { color: #475569 !important; }
.result-card { background: #FFFFFF; border: 1px solid #059669; border-radius: 12px;
    padding: 1.5rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.result-card h4 { color: #059669 !important; }
.result-card p { color: #334155 !important; }
</style>
""", unsafe_allow_html=True)

with st.expander("📋 Required File Format", expanded=False):
    st.markdown("""
    Your file must contain these columns (flexible naming):

    | Required Column | Accepted Aliases |
    |---|---|
    | `invoice_no` | invoice_number, invoice #, invoice_num |
    | `client_name` | customer_name, customer, client |
    | `client_email` | email, contact_email, customer_email |
    | `amount` | amount_due, total_amount, invoice_amount |
    | `due_date` | payment_due_date, due |

    **Optional:** `follow_up_count`, `status`
    """)
    sample = pd.DataFrame([{
        "invoice_no": "INV-2024-001", "client_name": "Rajesh Kapoor",
        "client_email": "rajesh@company.com", "amount": 45000, "due_date": "2025-04-10",
    }])
    st.dataframe(sample, hide_index=True)

st.markdown("""
<div class="upload-zone">
    <div class="upload-icon">📁</div>
    <p class="upload-text">Drag & drop your CSV or Excel file below</p>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"],
    help="Upload CSV or Excel files.", label_visibility="collapsed")

if uploaded:
    st.markdown("---")
    st.markdown("### 👁️ File Preview")
    try:
        preview_df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
        st.dataframe(preview_df.head(10), use_container_width=True, hide_index=True)
        st.markdown(f"**Total rows:** {len(preview_df)} · **Columns:** {', '.join(preview_df.columns)}")
        uploaded.seek(0)
    except Exception as e:
        st.error(f"Could not preview: {e}")

    if st.button("📤 Import to Database", type="primary", use_container_width=True):
        with st.spinner("Uploading..."):
            try:
                uploaded.seek(0)
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/octet-stream")}
                resp = requests.post(f"{BASE_URL}/api/invoices/upload", files=files, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    st.markdown(f"""
                    <div class="result-card">
                        <h4>✅ Upload Successful</h4>
                        <p><strong>File:</strong> {result.get('filename', 'N/A')}</p>
                        <p><strong>Total Rows:</strong> {result.get('total_rows', 0)}</p>
                        <p><strong>Inserted:</strong> {result.get('inserted', 0)}</p>
                        <p><strong>Skipped (Duplicates):</strong> {result.get('skipped_duplicates', 0)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if result.get("errors"):
                        st.warning("Some rows had errors:")
                        for err in result["errors"]:
                            st.text(f"  • {err}")
                else:
                    try: error_detail = resp.json().get("detail", resp.text)
                    except: error_detail = resp.text
                    st.error(f"Upload failed (HTTP {resp.status_code}): {error_detail}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Is the API running on port 8000?")
            except Exception as e:
                st.error(f"Upload failed: {e}")

st.markdown("---")
st.markdown("### 📊 Current Invoice Data")

invoices = get_invoices()
if isinstance(invoices, list) and invoices:
    df = pd.DataFrame(invoices)
    cols = [c for c in ["invoice_no", "client_name", "client_email", "amount", "due_date",
                         "status", "balance_amount", "days_overdue", "current_stage"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True,
        column_config={
            "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
            "balance_amount": st.column_config.NumberColumn("Balance (₹)", format="₹%.2f"),
            "days_overdue": "Days Overdue", "current_stage": "Stage",
        })
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Total", len(invoices))
    sc2.metric("Pending", len([i for i in invoices if i.get("status") == "PENDING"]))
    sc3.metric("Partial", len([i for i in invoices if i.get("status") == "PARTIAL"]))
    sc4.metric("Paid", len([i for i in invoices if i.get("status") == "PAID"]))
    # Clear data button
    st.markdown("---")
    with st.expander("🗑️ Danger Zone", expanded=False):
        st.warning("This will permanently delete ALL invoices, payments, follow-up logs, and responses.")
        if st.button("🗑️ Clear All Data", type="primary", use_container_width=True):
            with st.spinner("Clearing..."):
                result = clear_all_data()
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success("✅ All data cleared!")
                st.rerun()
elif isinstance(invoices, dict) and "error" in invoices:
    st.error(f"⚠️ {invoices['error']}")
else:
    st.info("No invoices in database. Upload a file to get started!")
