"""
AIChatLegal - Legal Workbench Component
Empowers Lawyers & Compliance Officers to inspect Sales submissions, review Gemini risk breakdowns,
attach legal advice, and enforce banking regulatory compliance.
"""

import streamlit as st
import json
from database import db_manager

def render_legal_view():
    st.markdown("## ⚖️ Legal Counsel & Compliance Workbench")
    st.caption("Review incoming sales policy uploads, inspect Gemini AI risk vectors, attach legally binding opinions, and issue contract riders.")

    policies = db_manager.get_all_policies()
    if not policies:
        st.info("No policy proposals available for review.")
        return

    # Select Policy to Review
    policy_options = {f"{p.get('policy_code')} - {p.get('client_name')} (${float(p.get('deal_value_usd',0)):,.2f}) [{p.get('status')}]": p.get("id") for p in policies}
    selected_label = st.selectbox("Select Deal / Policy Proposal for Legal Evaluation", list(policy_options.keys()))
    selected_id = policy_options[selected_label]

    policy_full = db_manager.get_policy_by_id(selected_id)
    if not policy_full:
        st.error("Failed to load policy details.")
        return

    # Layout: Left column policy text & Gemini risk, Right column lawyer input form
    col_left, col_right = st.columns([6, 5])

    with col_left:
        st.markdown(f"### Proposal: {policy_full.get('title')}")
        
        # Meta pills
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"**Client**: `{policy_full.get('client_name')}`")
        m2.markdown(f"**Deal Value**: `${float(policy_full.get('deal_value_usd', 0)):,.2f}`")
        m3.markdown(f"**Sales Lead**: `{policy_full.get('sales_rep_name')}`")

        st.markdown("#### Document Text & Policy Clauses")
        st.code(policy_full.get("raw_content", ""), language="markdown")

        # Risk Score Card if available
        risk = policy_full.get("risk_score")
        if risk:
            st.markdown("---")
            st.markdown("#### 🤖 Gemini AI Legal Risk Assessment")
            
            r_col1, r_col2 = st.columns(2)
            r_score = risk.get("overall_risk_score", 50)
            r_level = risk.get("risk_level", "medium").upper()
            
            r_col1.metric("Overall Risk Score", f"{r_score} / 100")
            r_col2.metric("Risk Classification", r_level)
            
            st.markdown(f"**AI Recommendation**: {risk.get('ai_recommendation')}")
            
            flagged = risk.get("flagged_clauses", [])
            if isinstance(flagged, str):
                try:
                    flagged = json.loads(flagged)
                except Exception:
                    flagged = [flagged]
                    
            if flagged:
                st.markdown("**Flagged Compliance Vectors**:")
                for item in flagged:
                    st.markdown(f"- ⚠️ `{item}`")

    with col_right:
        st.markdown("### 📝 Lawyer Advice & Regulatory Decision")
        
        with st.form("legal_advice_form"):
            lawyer_name = st.text_input("Reviewing Legal Counsel Name*", value="Eleanor Vance (Senior Legal Counsel, Global Banking)")
            
            decision = st.selectbox(
                "Formal Legal Decision / Status*",
                ["approved_with_riders", "pending_legal_review", "flagged_high_risk", "fully_approved", "rejected"],
                format_func=lambda x: {
                    "approved_with_riders": "🟢 Approve with Conditional Riders",
                    "pending_legal_review": "🟡 Request Further Compliance Clarification",
                    "flagged_high_risk": "🔴 Flag High Risk - Escalate to General Counsel",
                    "fully_approved": "✅ Fully Approved (Standard Terms)",
                    "rejected": "❌ Reject Proposal (Non-Compliant)"
                }[x]
            )

            advice_summary = st.text_area(
                "Legal Advice & Counsel Opinion*",
                height=140,
                value="Approved subject to inclusion of Standard Credit Risk Rider Schedule C. The requested SOFR margin discount is acceptable provided total client cross-sell deposit volume exceeds $50M annually."
            )

            required_riders_input = st.text_area(
                "Required Contract Riders (One per line)",
                height=90,
                value="Schedule 14B - Cross-Border Dispute & LCIA Arbitration Clause\nSchedule 4C - Minimum DSCR Baseline 1.20x Floor"
            )

            compliance_directives_input = st.text_area(
                "Regulatory Compliance Directives (OCC / SEC / GDPR)",
                height=80,
                value="File SEC Form 8-K disclosure if deal size exceeds 5% of net bank capital.\nVerify foreign counterparty AML/KYC sanction clearing."
            )

            submit_advice = st.form_submit_button("⚖️ Submit Official Legal Opinion & Update Policy Status", type="primary", use_container_width=True)

            if submit_advice:
                riders_list = [r.strip() for r in required_riders_input.split("\n") if r.strip()]
                directives_list = [d.strip() for d in compliance_directives_input.split("\n") if d.strip()]
                
                advice_payload = {
                    "policy_id": selected_id,
                    "lawyer_name": lawyer_name,
                    "advice_summary": advice_summary,
                    "required_riders": riders_list,
                    "compliance_directives": directives_list,
                    "decision": decision
                }
                
                db_manager.add_legal_advice(advice_payload)
                st.success("✅ Legal opinion & binding advice recorded! Policy status updated.")
                st.rerun()

        # Display Existing Opinions
        existing_advice = policy_full.get("advice", [])
        if existing_advice:
            st.markdown("---")
            st.markdown("#### 📜 Existing Legal Counsel Opinions")
            for adv in existing_advice:
                with st.expander(f"Advice by {adv.get('lawyer_name')} ({adv.get('created_at')[:10] if adv.get('created_at') else ''})"):
                    st.write(f"**Decision**: `{adv.get('decision')}`")
                    st.write(f"**Opinion**: {adv.get('advice_summary')}")
