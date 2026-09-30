import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* Base Theme */
        .stApp {
            background-color: #1a1a1a;
            color: #ffffff;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        
        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Premium Typography & Colors */
        h1, h2, h3, h4, h5, h6, p, span {
            color: #eeeeee;
        }
        
        .accent-text {
            color: #00d2ff;
        }
        
        /* Cards */
        .status-card {
            background: #252525;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .status-card-green { border-left: 4px solid #10b981; }
        .status-card-amber { border-left: 4px solid #f59e0b; }
        .status-card-red { border-left: 4px solid #ef4444; }
        .status-card-blue { border-left: 4px solid #3b82f6; }
        .status-card-neutral { border-left: 4px solid #6b7280; }
        
        .status-icon { font-size: 1.2rem; margin-right: 8px; }
        .status-title { font-weight: 600; font-size: 0.9rem; letter-spacing: 0.5px; text-transform: uppercase; color: #a1a1aa; }
        .status-value { font-size: 1.1rem; font-weight: 500; margin-top: 4px; color: #f4f4f5; }
        
        /* Analysis & Repair Boxes */
        .ai-analysis-box {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin-top: 15px;
            margin-bottom: 15px;
        }
        
        .repair-box {
            background: #252525;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 20px;
        }
        
        /* Smooth hover for native containers acting as cards */
        div[data-testid="stVerticalBlock"] > div > div > div > div > div[data-testid="stVerticalBlock"] {
            transition: all 0.2s ease;
        }
        div[data-testid="stVerticalBlock"] > div > div > div > div > div[data-testid="stVerticalBlock"]:hover {
            border-color: #3b82f6;
        }
        
        </style>
    """, unsafe_allow_html=True)

def status_card(title, value, state="neutral"):
    class_map = {
        "healthy": "status-card-green",
        "warning": "status-card-amber",
        "critical": "status-card-red",
        "ai": "status-card-blue",
        "neutral": "status-card-neutral"
    }
    css_class = class_map.get(state, "status-card-neutral")
    st.markdown(f"""
        <div class="status-card {css_class}">
            <div class="status-title">{title}</div>
            <div class="status-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def ai_analysis_card(content):
    st.markdown(f"""
        <div class="ai-analysis-box">
            <div style="color: #60a5fa; font-weight: 600; margin-bottom: 10px; font-size: 0.9rem; letter-spacing: 1px;">✦ FIXIT AI ANALYSIS</div>
            <div style="font-size: 1.05rem; line-height: 1.5;">{content}</div>
        </div>
    """, unsafe_allow_html=True)

