import streamlit as st
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from ui.components import load_css
from ui.dashboard import render_dashboard
from ui.diagnostics import render_diagnostics
from ui.troubleshooting import render_troubleshooting
from core.hardware_detection import detect_hardware
from core.ai_engine import LocalAIEngine

st.set_page_config(page_title="FixIt AI", layout="wide", initial_sidebar_state="expanded")
load_css()

# Handle programatic navigation
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Overview"

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='margin-bottom: 0;'>FIXIT AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9ca3af; font-size: 0.9rem; margin-top: 0;'>Offline AI Technician</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Custom Nav
    if st.button("◉ Overview", use_container_width=True): st.session_state["nav_page"] = "Overview"
    if st.button("◉ Diagnose", use_container_width=True): st.session_state["nav_page"] = "Diagnose"
    if st.button("◉ Troubleshoot", use_container_width=True): st.session_state["nav_page"] = "Troubleshoot"
    
    st.markdown("---")
    
    hw = detect_hardware()
    ai = LocalAIEngine()
    info = ai.get_active_backend_info()
    
    st.markdown("**SYSTEM**")
    st.markdown(f"<span style='color:#ccc; font-size: 0.9em;'>{hw['os']}<br>{hw['architecture']}</span>", unsafe_allow_html=True)
    
    st.markdown("<br>**AI**", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#ccc; font-size: 0.9em;'>● Local ({info['backend']})</span>", unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("● **OFFLINE READY**", unsafe_allow_html=True)

# Top Header
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("<h3 style='margin:0;'>FIXIT AI</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9ca3af; margin:0;'>Your laptop's offline AI technician</p>", unsafe_allow_html=True)
with col2:
    st.markdown("<div style='text-align: right; color: #10b981; font-weight: 600;'>● Local AI &nbsp;&nbsp; ● Offline Ready</div>", unsafe_allow_html=True)
st.markdown("---")

# Router
page = st.session_state["nav_page"]
if page == "Overview":
    render_dashboard()
elif page == "Diagnose":
    render_diagnostics()
elif page == "Troubleshoot":
    render_troubleshooting()
