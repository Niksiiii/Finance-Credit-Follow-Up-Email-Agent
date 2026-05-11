"""
📋 Audit Logs — Full audit trail of all follow-up communications.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import get_followup_logs
from utils.theme import BANKING_THEME, page_header, sidebar_branding

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent — Audit Logs", page_icon="📋", layout="wide")
st.markdown(BANKING_THEME, unsafe_allow_html=True)
sidebar_branding()
page_header("📋", "Audit Logs", "Complete audit trail of every follow-up email generated and sent")

st.markdown("""
<style>
.log-stat { background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 1rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.log-stat-val { font-size: 1.5rem; font-weight: 700; }
.log-stat-label { font-size: 0.8rem; color: #475569 !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Filters
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filter_invoice = st.text_input("🔍 Filter by Invoice #", placeholder="e.g. INV-2024-001")
with col_f2:
    filter_stage = st.selectbox("Stage", [None, 0, 1, 2, 3, 4, 5],
        format_func=lambda x: "All Stages" if x is None else f"Stage {x}" if x > 0 else "Thank You")
with col_f3:
    filter_status = st.selectbox("Send Status", [None, "DRY_RUN", "SENT", "FAILED", "ESCALATED"],
        format_func=lambda x: "All Statuses" if x is None else x)

logs = get_followup_logs(
    invoice_no=filter_invoice if filter_invoice else None,
    stage=filter_stage, send_status=filter_status,
)

if isinstance(logs, dict) and "error" in logs:
    st.error(f"⚠️ {logs['error']}")
    st.stop()

if isinstance(logs, list) and logs:
    df = pd.DataFrame(logs)

    c1, c2, c3, c4 = st.columns(4)
    total = len(df)
    dry = len(df[df["send_status"] == "DRY_RUN"]) if "send_status" in df.columns else 0
    sent = len(df[df["send_status"] == "SENT"]) if "send_status" in df.columns else 0
    failed = len(df[df["send_status"] == "FAILED"]) if "send_status" in df.columns else 0

    for col, label, val, color in [
        (c1, "Total Logs", total, "#1D4ED8"),
        (c2, "Dry-Run", dry, "#D97706"),
        (c3, "Sent", sent, "#059669"),
        (c4, "Failed", failed, "#DC2626"),
    ]:
        col.markdown(f'<div class="log-stat"><div class="log-stat-val" style="color:{color}">{val}</div>'
                     f'<div class="log-stat-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    display_cols = ["sent_at", "invoice_no", "client_name", "amount", "stage", "tone", "send_status", "email_subject"]
    available = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available], use_container_width=True, hide_index=True,
        column_config={
            "sent_at": st.column_config.DatetimeColumn("Timestamp", format="DD/MM/YYYY HH:mm:ss"),
            "invoice_no": "Invoice #", "client_name": "Client",
            "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
            "stage": "Stage", "tone": "Tone", "send_status": "Status", "email_subject": "Subject",
        })

    st.markdown("### 📧 View Full Email")
    log_opts = {f"[{l['send_status']}] {l.get('invoice_no','')} — Stage {l['stage']} ({l['sent_at'][:16] if l.get('sent_at') else 'N/A'})": i
                for i, l in enumerate(logs)}
    selected = st.selectbox("Select a log entry:", list(log_opts.keys()))

    if selected:
        entry = logs[log_opts[selected]]
        st.markdown(f"**To:** {entry.get('recipient_email', 'N/A')}")
        st.markdown(f"**Subject:** {entry.get('email_subject', 'N/A')}")
        st.markdown(f"**Tone:** {entry.get('tone', 'N/A')} · **Status:** {entry.get('send_status', 'N/A')}")
        if entry.get("error_message"):
            st.error(f"Error: {entry['error_message']}")
        st.text_area("Email Body", value=entry.get("email_body", ""), height=300, disabled=True)

    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button("📥 Export Logs as CSV", data=csv, file_name="audit_logs.csv", mime="text/csv")
else:
    st.info("No audit logs found. Trigger the agent from the Follow-Ups page.")
