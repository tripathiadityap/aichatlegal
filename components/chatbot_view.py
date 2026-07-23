"""
AIChatLegal - Gemini Chatbot Component
Interactive multi-turn AI legal advisor powered by Google Gemini for Sales & Legal teams.
"""

import streamlit as st
from database import db_manager
from gemini_engine import gemini_engine

def render_chatbot_view(current_role: str):
    st.markdown("## 🤖 Gemini Legal AI Assistant & Chatbot")
    st.caption("Ask natural language questions about uploaded deal policies, legal counsel advice, banking regulations, and credit risk guidelines.")

    policies = db_manager.get_all_policies()
    
    # Policy Context Selector
    col_sel, col_role = st.columns([3, 1])
    with col_sel:
        policy_options = {"[General Banking Policy & Regulations]": None}
        for p in policies:
            policy_options[f"{p.get('policy_code')} - {p.get('client_name')}"] = p.get("id")
        
        selected_key = st.selectbox("Attach Active Policy Context to Chat", list(policy_options.keys()))
        selected_id = policy_options[selected_key]
        
        selected_policy_ctx = None
        if selected_id:
            selected_policy_ctx = db_manager.get_policy_by_id(selected_id)

    with col_role:
        st.markdown(f"**Persona**: `{current_role.upper()}`")

    st.markdown("---")

    # Quick prompt suggestion pills
    st.markdown("**Suggested Quick Inquiries**:")
    s_col1, s_col2, s_col3 = st.columns(3)
    p1 = s_col1.button("📋 What riders are required for this deal?", use_container_width=True)
    p2 = s_col2.button("⚠️ Summarize key legal risk factors", use_container_width=True)
    p3 = s_col3.button("🔒 Explain banking security & compliance", use_container_width=True)

    # Initialize chat history in session state if missing
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": f"Welcome to **AIChatLegal**. I am your Gemini-powered Legal & Regulatory Advisor. How can I assist you with your policy uploads or legal counsel reviews today?"
            }
        ]

    # Process quick buttons
    triggered_query = None
    if p1:
        triggered_query = "What specific contract riders and compliance directives do our lawyers require for this proposal?"
    elif p2:
        triggered_query = "Summarize the primary legal and regulatory risk factors identified by Gemini AI for this upload."
    elif p3:
        triggered_query = "How does AIChatLegal ensure banking security, encryption, and zero data retention compliance?"

    # Display past chat messages
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user", avatar="💼").write(msg["content"])
        else:
            st.chat_message("assistant", avatar="🤖").write(msg["content"])

    # Chat Input Box
    user_input = st.chat_input("Ask Gemini Legal AI a question about policy terms, lawyer advice, or compliance...")
    query_to_send = triggered_query if triggered_query else user_input

    if query_to_send:
        # Append User Message
        st.session_state.chat_history.append({"role": "user", "content": query_to_send})
        st.chat_message("user", avatar="💼").write(query_to_send)

        # Generate Assistant Response
        with st.spinner("Gemini AI retrieving policy vectors and legal precedent..."):
            ai_response = gemini_engine.generate_chat_response(
                user_role=current_role,
                user_query=query_to_send,
                chat_history=st.session_state.chat_history,
                policy_context=selected_policy_ctx
            )

        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.chat_message("assistant", avatar="🤖").write(ai_response)
        st.rerun()
