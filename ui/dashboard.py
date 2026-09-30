import streamlit as st
from ui.components import status_card
from core.hardware_detection import detect_hardware
from core.ai_engine import LocalAIEngine

def render_dashboard():
    # Hero Section
    st.markdown("<h1 style='text-align: center; font-size: 3rem; margin-top: 2rem;'>FIXIT AI</h1>", unsafe_allow_html=True)
    st.markdown("""
        <h3 style='text-align: center; color: #e5e7eb; font-weight: 400;'>
            If anything on your Windows laptop stops working,<br>FixIt AI diagnoses it.
        </h3>
    """, unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align: center; color: #9ca3af; font-size: 1.1rem; margin-bottom: 3rem;'>
            Diagnose problems locally, understand what went wrong,<br>and safely recover your laptop — even without internet.
        </p>
    """, unsafe_allow_html=True)
    
    # Primary Buttons
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 2, 2, 1])
    with col_btn2:
        if st.button("DIAGNOSE MY LAPTOP", type="primary", use_container_width=True):
            st.session_state["nav_page"] = "Diagnose"
            st.rerun()
    with col_btn3:
        if st.button("CHECK NETWORK", use_container_width=True):
            st.session_state["nav_page"] = "Diagnose"
            st.session_state["trigger_network_scan"] = True
            st.rerun()
            
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # System Status Cards
    hw = detect_hardware()
    ai = LocalAIEngine()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        status_card("SYSTEM", "✓ Healthy", "healthy")
    with col2:
        net_status = "⚠ Offline" if 'last_diagnosis' in st.session_state and not st.session_state['last_diagnosis'].get('internet_connected', True) else "✓ Connected"
        net_state = "warning" if "Offline" in net_status else "healthy"
        status_card("NETWORK", net_status, net_state)
    with col3:
        status_card("AUDIO", "✓ Working", "healthy")
    with col4:
        status_card("AI ENGINE", "● Local AI", "ai")
    with col5:
        proc_str = "Snapdragon ARM64" if hw['is_snapdragon'] else f"Intel {hw['architecture']}"
        status_card("HARDWARE", proc_str, "neutral")
