"""
AIChatLegal - Analytics & Audit Trail Component
Provides executive reporting for Sales Repo Heads & Risk Committees with Plotly charts
and immutable regulatory audit trails.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database import db_manager

def render_analytics_view():
    st.markdown("## 📊 Executive Analytics & Audit Control")
    st.caption("High-level oversight for Sales Repo Heads, General Counsel, and Chief Compliance Officers.")

    policies = db_manager.get_all_policies()
    if not policies:
        st.info("No policy proposals recorded.")
        return

    # Key Financial Metrics Row
    total_deals = len(policies)
    total_val = sum([float(p.get("deal_value_usd", 0)) for p in policies])
    approved_count = len([p for p in policies if p.get("status") in ["approved_with_riders", "fully_approved"]])
    flagged_count = len([p for p in policies if p.get("status") == "flagged_high_risk"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Proposals", f"{total_deals}", delta="Active Pipeline")
    k2.metric("Total Deal Volume", f"${total_val / 1e6:.1f}M", delta="Capital Value")
    k3.metric("Approved / Clearance", f"{approved_count}", delta=f"{(approved_count/total_deals)*100:.0f}% Rate")
    k4.metric("High Risk Escalations", f"{flagged_count}", delta="Legal Attention Required")

    st.markdown("---")

    # Plotly Charts
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Policy Status Distribution")
        status_counts = pd.DataFrame([p.get("status") for p in policies], columns=["Status"]).value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        
        fig1 = px.pie(
            status_counts, 
            values="Count", 
            names="Status", 
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.45
        )
        fig1.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown("#### Capital Allocation by Product Line ($ Value)")
        cat_df = pd.DataFrame([{"Category": p.get("product_category"), "Value": float(p.get("deal_value_usd", 0))} for p in policies])
        cat_grouped = cat_df.groupby("Category").sum().reset_index()
        
        fig2 = px.bar(
            cat_grouped, 
            x="Category", 
            y="Value", 
            labels={"Value": "Deal Volume ($)"},
            color="Category",
            color_discrete_sequence=px.colors.sequential.Indigo
        )
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Audit Trail Table
    st.markdown("### 🔒 Immutable Banking Regulatory Audit Log (OCC / CFPB / SEC)")
    st.caption("Appended audit trail tracking every document upload, Gemini analysis execution, and legal counsel sign-off.")
    
    logs = db_manager.get_audit_logs(limit=30)
    if logs:
        audit_df = pd.DataFrame(logs)
        cols = ["created_at", "actor_name", "actor_role", "action_type", "ip_address"]
        audit_display = audit_df[[c for c in cols if c in audit_df.columns]]
        st.dataframe(audit_display, use_container_width=True, hide_index=True)
    else:
        st.info("No audit entries logged yet.")
