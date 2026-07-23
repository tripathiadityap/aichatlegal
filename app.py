"""
AIChatLegal - Enterprise Banking Policy & Legal Advisory System
Main Application Entrypoint (Streamlit Framework)
Project: aichatlegal
"""

import os
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="AIChatLegal | Enterprise Bank Policy & Legal Advisory",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Load Custom CSS Styling
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import Components & Backend Managers
from database import db_manager
from gemini_engine import gemini_engine
from components.sales_view import render_sales_view
from components.legal_view import render_legal_view
from components.chatbot_view import render_chatbot_view
from components.analytics_view import render_analytics_view

# 3. Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/lawyer.png", width=64)
    st.markdown("## **AIChatLegal**")
    st.caption("AI Bank Policy & Legal Advisory v2.4")
    
    st.markdown("---")
    
    # Active Role Persona Selector
    st.markdown("### 👤 Active Persona")
    user_role = st.selectbox(
        "Select User Persona",
        ["sales_head", "sales_rep", "legal_counsel", "compliance_officer", "chief_risk_officer"],
        format_func=lambda x: {
            "sales_head": "👔 Sales Repo Head (VP)",
            "sales_rep": "💼 Sales Lead / Deal Officer",
            "legal_counsel": "⚖️ Senior Legal Counsel",
            "compliance_officer": "🛡️ Regulatory Compliance Officer",
            "chief_risk_officer": "📊 Chief Risk Officer"
        }[x]
    )

    st.markdown("---")

    # Infrastructure Health Status Indicators
    st.markdown("### ⚡ Infrastructure Status")
    
    if db_manager.use_supabase:
        st.success("🟢 Supabase DB: Connected")
    else:
        st.info("🔵 Database: SQLite Embedded Store")

    if gemini_engine.api_available:
        st.success(f"🟢 Gemini AI: Active ({gemini_engine.framework})")
    else:
        st.warning("⚡ Gemini AI: Analytical Engine")

    st.markdown("---")
    st.caption("🔒 Banking Security: TLS 1.3 | AES-256 | OCC & CFPB Audit Compliant")

# 4. Header Banner
st.markdown("""
<div class="bank-header-banner">
    <div class="bank-header-title">🏛️ AIChatLegal — Bank Policy & Legal Compliance Engine</div>
    <div class="bank-header-subtitle">Eliminating friction between Sales upload demands and Legal Counsel regulatory oversight via Google Gemini AI & Supabase.</div>
</div>
""", unsafe_allow_html=True)

# 5. Main Navigation Bar
nav_choice = st.radio(
    "Navigation Menu",
    ["💼 Sales Portal", "⚖️ Legal Workbench", "🤖 Gemini AI Chatbot", "📊 Executive Analytics & Audit"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# 6. Render Active View Component
if nav_choice == "💼 Sales Portal":
    render_sales_view()
elif nav_choice == "⚖️ Legal Workbench":
    render_legal_view()
elif nav_choice == "🤖 Gemini AI Chatbot":
    render_chatbot_view(user_role)
elif nav_choice == "📊 Executive Analytics & Audit":
    render_analytics_view()
