"""
📧 Follow-Ups — Overdue queue, trigger agent, automation scheduler.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import (
    get_invoices, trigger_followups, preview_email, get_config,
    start_automation, stop_automation, get_automation_status,
)
from utils.theme import BANKING_THEME, page_header, sidebar_branding

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent — Follow-Ups", page_icon="📧", layout="wide")
st.markdown(BANKING_THEME, unsafe_allow_html=True)
sidebar_branding()
page_header("📧", "Follow-Up Queue", "View overdue invoices, trigger the AI agent, or enable automation")

st.markdown("""
<style>
.stage-badge { display: inline-block; padding: 4px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; }
.stage-1 { background: #DCFCE7; color: #166534 !important; }
.stage-2 { background: #FEF3C7; color: #92400E !important; }
.stage-3 { background: #FFEDD5; color: #9A3412 !important; }
.stage-4 { background: #FEE2E2; color: #991B1B !important; }
.stage-5 { background: #FDE8E8; color: #7F1D1D !important; }
.email-preview { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 1.5rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.email-subject { font-size: 1.05rem; font-weight: 600; color: #0F2A4A !important; margin-bottom: 0.5rem; }
.email-body { color: #334155 !important; white-space: pre-wrap; line-height: 1.7; font-size: 0.9rem; }
.auto-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 1.5rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.auto-card h4 { color: #0F2A4A !important; } .auto-card p { color: #334155 !important; }
.auto-running { border-color: #059669; border-width: 2px; }
.auto-stopped { border-color: #CBD5E1; }
.pulse { display: inline-block; width: 10px; height: 10px; border-radius: 50%; animation: pulse 2s infinite; }
.pulse-green { background: #059669; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

config = get_config()
if isinstance(config, dict) and "error" not in config:
    mode = "🟢 DRY-RUN" if config.get("dry_run_mode") else "🔴 LIVE"
    st.caption(f"**Mode:** {mode} · **LLM:** {config.get('llm_model', 'N/A')} · **Sender:** {config.get('sender_email', 'N/A')}")

st.markdown("---")

# ── Automation Scheduler ─────────────────────────────────
st.markdown("### 🤖 Automation Scheduler")
auto_status = get_automation_status()
is_auto_running = isinstance(auto_status, dict) and auto_status.get("is_running", False)
auto_class = "auto-running" if is_auto_running else "auto-stopped"

if is_auto_running:
    st.markdown(f"""
    <div class="auto-card {auto_class}">
        <h4 style="color:#059669 !important;"><span class="pulse pulse-green"></span> Automation ACTIVE</h4>
        <p>⏱️ Interval: <strong>{auto_status.get('interval_hours', 24)}h</strong> ·
           Mode: <strong>{'DRY-RUN' if auto_status.get('dry_run') else 'LIVE'}</strong></p>
        <p>📅 Next: <strong>{auto_status.get('next_run', 'N/A')}</strong> ·
           Last: <strong>{auto_status.get('last_run', 'Never')}</strong> ·
           Runs: <strong>{auto_status.get('total_runs', 0)}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🛑 Stop Automation", type="primary", use_container_width=True):
        result = stop_automation()
        st.success("✅ Stopped") if "error" not in result else st.error(result['error'])
        st.rerun()
else:
    st.markdown(f"""
    <div class="auto-card {auto_class}">
        <h4 style="color:#475569 !important;">⚫ Automation is OFF</h4>
        <p>Configure and start to auto-send follow-ups at regular intervals.</p>
    </div>
    """, unsafe_allow_html=True)
    ac1, ac2, ac3 = st.columns([2, 1, 1])
    with ac1:
        interval = st.selectbox("Run Every", [
            ("Every 1 hour", 1.0), ("Every 6 hours", 6.0), ("Every 12 hours", 12.0),
            ("Every 24 hours (Daily)", 24.0), ("Every 48 hours", 48.0), ("Weekly", 168.0),
        ], format_func=lambda x: x[0], index=3)
    with ac2:
        auto_dry_run = st.toggle("Dry-Run", value=True, key="auto_dry_run", help="OFF = sends REAL emails")
    with ac3:
        st.markdown("")
        if st.button("🚀 Start Automation", type="primary", use_container_width=True):
            result = start_automation(interval_hours=interval[1], dry_run=auto_dry_run)
            st.success(f"✅ Started! Every {interval[1]}h") if "error" not in result else st.error(result['error'])
            st.rerun()
    if not auto_dry_run:
        st.warning("⚠️ **LIVE MODE**: Emails will be sent via SMTP.")

st.markdown("---")

# ── Manual Trigger ───────────────────────────────────────
st.markdown("### ⚡ One-Time Agent Trigger")
col_t, col_m = st.columns([3, 1])
with col_m:
    dry_run = st.toggle("Dry-Run Mode", value=True, help="OFF = real emails", key="manual_dry_run")
    if not dry_run:
        st.warning("⚠️ LIVE")
with col_t:
    if st.button("🚀 Run Follow-Up Agent Now", type="primary", use_container_width=True):
        with st.spinner("Running agent..."):
            result = trigger_followups(dry_run=dry_run)
        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.success(f"✅ Done! Processed: {result['total_processed']}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Sent", result.get("emails_sent", 0))
            m2.metric("Dry-Run", result.get("emails_dry_run", 0))
            m3.metric("Failed", result.get("emails_failed", 0))
            m4.metric("Escalated", result.get("escalated_to_legal", 0))
            if result.get("details"):
                with st.expander("📋 Details", expanded=True):
                    st.dataframe(pd.DataFrame(result["details"]), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Overdue Invoices ─────────────────────────────────────
st.markdown("### 📋 Overdue Invoices")
invoices = get_invoices(status="PENDING")
partial = get_invoices(status="PARTIAL")
all_inv = []
if isinstance(invoices, list): all_inv.extend(invoices)
if isinstance(partial, list): all_inv.extend(partial)
overdue = [i for i in all_inv if i.get("days_overdue", 0) > 0]

if overdue:
    df = pd.DataFrame(overdue)
    cols = [c for c in ["invoice_no", "client_name", "amount", "balance_amount", "due_date",
                        "days_overdue", "current_stage", "follow_up_count", "status"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True,
        column_config={
            "invoice_no": "Invoice #", "client_name": "Client",
            "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
            "balance_amount": st.column_config.NumberColumn("Balance (₹)", format="₹%.2f"),
            "due_date": "Due Date", "days_overdue": "Days Overdue",
            "current_stage": "Stage", "follow_up_count": "Follow-Ups", "status": "Status",
        })

    st.markdown("### 👁️ Preview Email")
    inv_options = {f"{i['invoice_no']} - {i['client_name']} ({i['days_overdue']}d)": i['id'] for i in overdue}
    selected = st.selectbox("Select invoice:", list(inv_options.keys()))
    if selected and st.button("Generate Preview"):
        with st.spinner("Generating via LLM..."):
            preview = preview_email(inv_options[selected])
        if "error" in preview:
            st.error(f"Error: {preview['error']}")
        else:
            badge = {1: "stage-1", 2: "stage-2", 3: "stage-3", 4: "stage-4", 5: "stage-5"}.get(preview.get("stage", 1), "stage-1")
            st.markdown(f'<span class="stage-badge {badge}">Stage {preview.get("stage")} — {preview.get("tone")}</span>'
                f' <span style="color:#475569; margin-left:1rem;">{preview.get("days_overdue", 0)} days overdue</span>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="email-preview">
                <div class="email-subject">📧 {preview.get('subject', '')}</div>
                <hr style="border-color:#E2E8F0;">
                <div class="email-body">{preview.get('body', '')}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success("🎉 No overdue invoices!")
