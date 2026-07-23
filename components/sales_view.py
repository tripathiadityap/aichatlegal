"""
AIChatLegal - Sales View Component
Handles Sales Representative & Sales Repo Head deal policy uploads, instant Gemini pre-screening,
and status tracking.
"""

import streamlit as st
import pandas as pd
from database import db_manager
from gemini_engine import gemini_engine

def render_sales_view():
    st.markdown("## 💼 Sales Portal & Policy Submission")
    st.caption("Sales Reps & Sales Repo Heads upload customer policy overrides, deal terms, or credit proposals for automated Gemini AI pre-screening and Legal Counsel review.")

    tabs = st.tabs(["🚀 Upload & Pre-Screen Deal", "📋 Submission Status & Track Record"])

    with tabs[0]:
        st.markdown("### New Sales Proposal Submission")
        
        with st.form("sales_upload_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Proposal / Deal Title*", value="Commercial Loan Rate Override - Horizon Logistics")
                client_name = st.text_input("Client Corporate Entity*", value="Horizon Logistics International LLC")
                sales_rep = st.text_input("Sales Lead Name*", value="Aditya Prakash (VP Commercial Sales)")
            
            with col2:
                deal_value = st.number_input("Deal Value (USD)*", min_value=100000.0, value=25000000.0, step=500000.0, format="%.2f")
                product_category = st.selectbox(
                    "Product / Financing Category*",
                    ["Syndicated Revolving Credit", "Commercial Credit Override", "Asset Securitization", "Structured Trade Finance", "Derivatives Override"]
                )
                sales_head_approval = st.checkbox("Sales Repo Head Pre-Approved", value=True, help="Check if Sales Repo Head has vetted commercial terms.")

            st.markdown("#### Contract & Policy Override Document Content")
            upload_option = st.radio("Input Source", ["Direct Policy Clause Input", "Simulated PDF Document Parse"], horizontal=True)

            if upload_option == "Direct Policy Clause Input":
                raw_content = st.text_area(
                    "Policy Text / Override Request*",
                    height=200,
                    value="""SECTION 3.1 - SOFR MARGIN DISCOUNT REQUEST
Client requests a 50 bps reduction on standard SOFR margin (1.75% vs Standard Baseline 2.25%) in exchange for exclusive global cash management relationship.

SECTION 8.4 - COVENANT RATIO EXEMPTION
Borrower leverage ratio ceiling requested at 4.00x EBITDA for the first 18 months post-closing.

SECTION 12.1 - INDEMNIFICATION LIMITATION
Client requests liability cap equal to 1.5x fee revenue in event of administrative trade settlement disputes."""
                )
            else:
                st.file_uploader("Upload Policy / Agreement Document (PDF, DOCX, TXT)", type=["pdf", "txt", "docx"])
                raw_content = """SECTION 1.1 - CREDIT LINE FACILITY OVERRIDE
Standard collateral haircut reduced from 20% to 12% for eligible accounts receivable under 60 days past due.

SECTION 15.2 - GOVERNING JURISDICTION
Governing law: State of New York. Dispute resolution via American Arbitration Association (AAA) in New York City."""

            submitted = st.form_submit_button("⚡ Run Gemini AI Pre-Screening & Submit to Legal", type="primary", use_container_width=True)

            if submitted:
                if not title or not client_name or not raw_content:
                    st.error("Please fill in all required fields (*).")
                else:
                    with st.spinner("Gemini AI evaluating policy compliance, regulatory risk, and bank covenant thresholds..."):
                        # Gemini AI risk analysis
                        risk_analysis = gemini_engine.analyze_policy_upload(title, client_name, deal_value, raw_content)
                        
                        # Save to Supabase / DB
                        policy_data = {
                            "title": title,
                            "client_name": client_name,
                            "deal_value_usd": deal_value,
                            "product_category": product_category,
                            "sales_rep_name": sales_rep,
                            "sales_head_approval": sales_head_approval,
                            "raw_content": raw_content,
                            "summary": risk_analysis.get("summary", "")
                        }
                        
                        policy_id = db_manager.insert_policy(policy_data, risk_analysis)
                        
                        st.success(f"✅ Policy Proposal submitted successfully! Assigned ID: `{policy_id[:8]}...`")
                        
                        # Display AI Pre-Screening Summary Card
                        st.markdown("---")
                        st.markdown("### 🤖 Gemini AI Pre-Screening Results")
                        
                        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                        score = risk_analysis.get("overall_risk_score", 50)
                        level = risk_analysis.get("risk_level", "medium").upper()
                        
                        r_col1.metric("Overall Risk Score", f"{score} / 100", delta="- High Risk" if score > 70 else "Normal Risk")
                        r_col2.metric("Regulatory Compliance", f"{risk_analysis.get('regulatory_compliance_score', 75)}%", delta="SEC/OCC Check")
                        r_col3.metric("Financial Exposure", f"{risk_analysis.get('financial_exposure_score', 60)}%", delta="Exposure Alert")
                        r_col4.metric("Risk Classification", level)
                        
                        st.info(f"**AI Recommendation**: {risk_analysis.get('ai_recommendation')}")
                        
                        if risk_analysis.get("flagged_clauses"):
                            st.warning("⚠️ **Flagged Risk Vectors for Lawyers**:\n- " + "\n- ".join(risk_analysis.get("flagged_clauses", [])))

    with tabs[1]:
        st.markdown("### Active Deal Submissions")
        policies = db_manager.get_all_policies()
        
        if not policies:
            st.info("No policy proposals found.")
        else:
            df_data = []
            for p in policies:
                status_raw = p.get("status", "pending_legal_review")
                if status_raw == "pending_legal_review":
                    status_fmt = "🟡 Pending Legal Review"
                elif status_raw == "approved_with_riders":
                    status_fmt = "🟢 Approved with Riders"
                elif status_raw == "flagged_high_risk":
                    status_fmt = "🔴 Flagged High Risk"
                else:
                    status_fmt = f"🔵 {status_raw.replace('_', ' ').title()}"

                df_data.append({
                    "Policy Code": p.get("policy_code", "N/A"),
                    "Client": p.get("client_name"),
                    "Proposal Title": p.get("title"),
                    "Deal Size ($)": f"${float(p.get('deal_value_usd', 0)):,.2f}",
                    "Product Category": p.get("product_category"),
                    "Sales Rep": p.get("sales_rep_name"),
                    "Status": status_fmt,
                    "Submitted": p.get("created_at")[:10] if p.get("created_at") else "N/A"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
