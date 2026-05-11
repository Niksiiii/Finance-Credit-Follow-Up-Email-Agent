"""
👥 Team — Payments, team management, response tracking.
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.api_client import (
    get_team_members, add_team_member, get_responses, create_response,
    update_response, get_invoices, record_payment, get_payments,
)
from utils.theme import BANKING_THEME, page_header, sidebar_branding

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent — Team", page_icon="👥", layout="wide")
st.markdown(BANKING_THEME, unsafe_allow_html=True)
sidebar_branding()
page_header("👥", "Team & Payments", "Manage payments, team members, and client responses")

st.markdown("""
<style>
.team-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
    padding: 0.8rem 1rem; margin: 0.4rem 0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.team-name { font-weight: 600; color: #0F2A4A !important; }
.team-role { color: #475569 !important; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💳 Payments", "👥 Team Members", "💬 Response Tracker"])

# ── Tab 1: Payments ───────────────────────────────────────
with tab1:
    st.markdown("### Record Payment & Send Thank You")
    st.markdown("Partial payment → thank-you with balance. 50%+ paid → stage reduced by 1.")

    invoices = get_invoices()
    if isinstance(invoices, list) and invoices:
        pending = [i for i in invoices if i.get("status") in ("PENDING", "PARTIAL")]
        if pending:
            inv_labels = []
            inv_map = {}
            for i in pending:
                bal = i.get("balance_amount")
                amt = bal if (bal is not None and bal > 0) else i["amount"]
                label = f"{i['invoice_no']} - {i['client_name']} (Due: ₹{amt:,.2f})"
                if i.get("status") == "PARTIAL":
                    label += " [PARTIAL]"
                inv_labels.append(label)
                inv_map[label] = i

            sel_label = st.selectbox("Select Invoice", inv_labels, key="pay_inv_sel")
            sel_inv = inv_map[sel_label]

            bal = sel_inv.get("balance_amount")
            has_balance = bal is not None and bal > 0
            balance_due = bal if has_balance else sel_inv["amount"]

            ic1, ic2, ic3, ic4 = st.columns(4)
            ic1.metric("Invoice Amount", f"₹{sel_inv['amount']:,.2f}")
            ic2.metric("Balance Due", f"₹{balance_due:,.2f}")
            ic3.metric("Days Overdue", f"{sel_inv.get('days_overdue', 0)}")
            ic4.metric("Status", sel_inv.get("status", "PENDING"))

            st.markdown("---")

            with st.form("record_payment_form", clear_on_submit=True):
                fc1, fc2 = st.columns(2)
                with fc1:
                    amount = st.number_input(
                        "Amount Received (₹)", min_value=1.0,
                        max_value=float(balance_due), value=min(1000.0, float(balance_due)),
                        step=500.0, help="Enter the actual amount received",
                    )
                with fc2:
                    pay_date = st.date_input("Payment Date", value=date.today())

                pay_ref = st.text_input("Payment Reference", placeholder="e.g. UTR number, cheque no.")

                dc1, dc2 = st.columns([3, 1])
                with dc2:
                    dry_run = st.toggle("Dry-Run", value=True, key="pay_dry_run", help="OFF = sends REAL email")
                with dc1:
                    if not dry_run:
                        st.warning("⚠️ LIVE: Email will be sent via SMTP!")

                submitted = st.form_submit_button("💳 Record Payment", type="primary", use_container_width=True)
                if submitted:
                    if amount <= 0:
                        st.error("Enter a valid amount > 0")
                    else:
                        data = {
                            "invoice_id": sel_inv["id"],
                            "amount_received": amount,
                            "payment_date": str(pay_date),
                            "payment_reference": pay_ref if pay_ref else "",
                        }
                        with st.spinner("Recording..."):
                            result = record_payment(data, dry_run=dry_run)
                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            is_partial = result.get("is_partial", False)
                            balance_rem = result.get("balance_remaining", 0)
                            if is_partial:
                                st.warning(f"✅ Partial payment ₹{amount:,.2f} recorded! Balance: ₹{balance_rem:,.2f}")
                            else:
                                st.success(f"✅ Full payment ₹{amount:,.2f} recorded! Invoice → PAID")
                            ty = result.get("thank_you", {})
                            st.info(f"📧 **{ty.get('thank_you_status', 'N/A')}** — {ty.get('subject', '')}")
        else:
            st.success("🎉 All invoices are fully paid!")
    else:
        st.info("No invoices loaded. Upload data first.")

    st.markdown("---")
    st.markdown("### 💰 Payment History")
    payments = get_payments()
    if isinstance(payments, list) and payments:
        df = pd.DataFrame(payments)
        cols = [c for c in ["invoice_no", "client_name", "original_amount", "amount_received",
                             "is_partial", "balance_remaining", "payment_date",
                             "payment_reference", "thank_you_sent"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True,
            column_config={
                "original_amount": st.column_config.NumberColumn("Invoice (₹)", format="₹%.2f"),
                "amount_received": st.column_config.NumberColumn("Paid (₹)", format="₹%.2f"),
                "balance_remaining": st.column_config.NumberColumn("Balance (₹)", format="₹%.2f"),
                "is_partial": st.column_config.CheckboxColumn("Partial?"),
                "thank_you_sent": st.column_config.CheckboxColumn("Email Sent"),
            })
    else:
        st.info("No payments recorded yet.")

# ── Tab 2: Team Members ──────────────────────────────────
with tab2:
    st.markdown("### Manage Finance Team")
    with st.expander("➕ Add New Member", expanded=False):
        with st.form("add_member"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            role = st.selectbox("Role", ["Executive", "Manager", "Legal"])
            if st.form_submit_button("Add Member", type="primary") and name and email:
                result = add_team_member({"name": name, "email": email, "role": role})
                st.success(f"✅ Added {name}") if "error" not in result else st.error(result['error'])
                st.rerun()

    members = get_team_members()
    if isinstance(members, list) and members:
        for m in members:
            st.markdown(f'<div class="team-card"><span class="team-name">{m["name"]}</span> — '
                f'<span class="team-role">{m["role"]}</span> · '
                f'<span style="color:#64748B !important">{m["email"]}</span></div>', unsafe_allow_html=True)
    else:
        st.info("No team members added yet.")

# ── Tab 3: Response Tracker ──────────────────────────────
with tab3:
    st.markdown("### Client Response Tracker")
    with st.expander("➕ Log New Response", expanded=False):
        invoices = get_invoices()
        if isinstance(invoices, list) and invoices:
            inv_opts = {f"{i['invoice_no']} - {i['client_name']}": i['id'] for i in invoices}
            with st.form("log_response"):
                sel_inv = st.selectbox("Invoice", list(inv_opts.keys()))
                resp_type = st.selectbox("Type", ["PROMISE_TO_PAY", "DISPUTE", "PARTIAL_PAYMENT", "NO_RESPONSE"])
                notes = st.text_area("Notes")
                members = get_team_members()
                member_names = [m['name'] for m in members] if isinstance(members, list) else []
                assigned = st.selectbox("Assign To", [""] + member_names)
                if st.form_submit_button("Log Response", type="primary"):
                    data = {"invoice_id": inv_opts[sel_inv], "response_type": resp_type,
                            "notes": notes, "assigned_to": assigned if assigned else None}
                    result = create_response(data)
                    st.success("✅ Logged") if "error" not in result else st.error(result['error'])
                    st.rerun()

    f1, _ = st.columns(2)
    with f1:
        filter_status = st.selectbox("Filter Status", [None, "OPEN", "IN_PROGRESS", "RESOLVED"],
            format_func=lambda x: "All" if x is None else x, key="resp_filter")

    responses = get_responses(action_status=filter_status)
    if isinstance(responses, list) and responses:
        df = pd.DataFrame(responses)
        cols = [c for c in ["invoice_no", "client_name", "response_type", "assigned_to",
                             "action_status", "notes", "updated_at"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)

        st.markdown("#### Update Response")
        resp_opts = {f"#{r['id']} {r.get('invoice_no', '')} — {r['response_type']} ({r['action_status']})": r['id'] for r in responses}
        sel_resp = st.selectbox("Select:", list(resp_opts.keys()))
        if sel_resp:
            uc1, uc2 = st.columns(2)
            with uc1: new_status = st.selectbox("Status", ["OPEN", "IN_PROGRESS", "RESOLVED"], key="upd_st")
            with uc2: new_notes = st.text_input("Notes", key="upd_notes")
            if st.button("Update", type="primary"):
                upd = {"action_status": new_status}
                if new_notes: upd["notes"] = new_notes
                result = update_response(resp_opts[sel_resp], upd)
                st.success("✅ Updated") if "error" not in result else st.error(result['error'])
                st.rerun()
    else:
        st.info("No responses logged yet.")
