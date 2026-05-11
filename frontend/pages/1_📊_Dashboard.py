"""
📊 Dashboard — KPIs, Charts, and Activity Feed.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import get_dashboard_stats, get_stage_distribution, get_revenue_timeline, get_followup_logs
from utils.theme import BANKING_THEME, page_header, sidebar_branding

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent — Dashboard", page_icon="📊", layout="wide")
st.markdown(BANKING_THEME, unsafe_allow_html=True)
sidebar_branding()
page_header("📊", "Dashboard", "KPIs, charts, and real-time financial overview")

# Extra dashboard-specific styles
st.markdown("""
<style>
.kpi-card {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 1.2rem 1rem; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease; overflow: hidden;
}
.kpi-card:hover { border-color: #3B82F6; box-shadow: 0 4px 12px rgba(59,130,246,0.12); transform: translateY(-1px); }
.kpi-label { font-size: 0.7rem; color: #475569 !important; text-transform: uppercase;
    letter-spacing: 1.2px; font-weight: 600; margin-bottom: 6px; }
.kpi-value { font-size: 1.4rem; font-weight: 700; margin: 0; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; }
.kpi-value-sm { font-size: 1.1rem; font-weight: 700; margin: 0; }
.kpi-blue { color: #1D4ED8 !important; } .kpi-red { color: #DC2626 !important; }
.kpi-green { color: #059669 !important; } .kpi-amber { color: #D97706 !important; }
.kpi-purple { color: #7C3AED !important; }
.section-header { color: #0F2A4A !important; font-size: 1.1rem; font-weight: 600;
    margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid #DBEAFE; }
</style>
""", unsafe_allow_html=True)

def format_currency(val):
    """Format large numbers with Lakhs/Cr suffix to prevent overflow."""
    if val >= 10000000:
        return f"₹{val/10000000:.1f} Cr"
    elif val >= 100000:
        return f"₹{val/100000:.1f} L"
    elif val >= 1000:
        return f"₹{val/1000:.1f}K"
    else:
        return f"₹{val:,.0f}"


stats = get_dashboard_stats()
if "error" in stats:
    st.error(f"⚠️ {stats['error']}")
    st.info("Start the backend: `cd backend && uvicorn app.main:app --reload`")
    st.stop()

# Row 1: Core KPIs
c1, c2, c3, c4, c5 = st.columns(5)
for col, label, val, cls, sm in [
    (c1, "Total Invoices", str(stats['total_invoices']), "blue", False),
    (c2, "Overdue", str(stats['total_overdue']), "red", False),
    (c3, "Recovered", format_currency(stats['total_amount_recovered']), "green", True),
    (c4, "Recovery Rate", f"{stats['recovery_rate']}%", "green", False),
    (c5, "Avg DSO", f"{stats['avg_days_outstanding']} days", "amber", False),
]:
    sc = "kpi-value-sm" if sm else "kpi-value"
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="{sc} kpi-{cls}">{val}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

# Row 2: Financial KPIs
c6, c7, c8, c9 = st.columns(4)
for col, label, val, cls in [
    (c6, "Overdue Amount", format_currency(stats['total_amount_overdue']), "red"),
    (c7, "Paid", str(stats['total_paid']), "green"),
    (c8, "Escalated", str(stats['total_escalated']), "amber"),
    (c9, "Follow-Ups Sent", str(stats['follow_ups_sent_total']), "purple"),
]:
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value kpi-{cls}">{val}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# Charts
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<p class="section-header">📊 Stage Distribution</p>', unsafe_allow_html=True)
    sd = get_stage_distribution()
    if isinstance(sd, list) and sd:
        df = pd.DataFrame(sd)
        fig = go.Figure(go.Pie(
            labels=df["tone"], values=df["count"], hole=0.55,
            marker_colors=["#059669", "#D97706", "#EA580C", "#DC2626", "#991B1B"][:len(df)],
            textinfo="label+value", textfont=dict(size=12, color="#334155"),
        ))
        fig.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            font_color="#334155", height=360, margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(font=dict(color="#334155")),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No overdue invoices yet.")

with ch2:
    st.markdown('<p class="section-header">💰 Revenue Recovered</p>', unsafe_allow_html=True)
    rv = get_revenue_timeline()
    if isinstance(rv, list) and rv:
        df = pd.DataFrame(rv)
        fig = go.Figure(go.Scatter(
            x=df["date"], y=df["cumulative"], mode="lines+markers",
            line=dict(color="#1D4ED8", width=3), fill="tozeroy",
            fillcolor="rgba(29,78,216,0.08)", marker=dict(color="#1D4ED8", size=8),
        ))
        fig.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#334155",
            xaxis=dict(gridcolor="#E2E8F0", title="Date", title_font=dict(color="#475569")),
            yaxis=dict(gridcolor="#E2E8F0", title="Amount (₹)", title_font=dict(color="#475569")),
            height=360, margin=dict(t=10, b=40, l=60, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No payments recorded yet.")

st.markdown("---")

# Recent Activity
st.markdown('<p class="section-header">📋 Recent Activity</p>', unsafe_allow_html=True)
logs = get_followup_logs()
if isinstance(logs, list) and logs:
    df = pd.DataFrame(logs[:15])
    cols = [c for c in ["sent_at", "invoice_no", "client_name", "stage", "tone", "send_status"] if c in df.columns]
    if cols:
        st.dataframe(df[cols], use_container_width=True, hide_index=True,
                     column_config={"sent_at": "Time", "invoice_no": "Invoice #",
                         "client_name": "Client", "stage": "Stage", "tone": "Tone", "send_status": "Status"})
else:
    st.info("No follow-up activity yet. Run the agent from the Follow-Ups page.")
