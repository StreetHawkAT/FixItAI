import streamlit as st
import time
from core.repair_engine import RepairEngine
from diagnostics.network import check_network
from core.ai_engine import LocalAIEngine
from ui.components import ai_analysis_card

def render_troubleshooting():
    if st.button("← Back"):
        st.session_state["nav_page"] = "Diagnose"
        st.rerun()

    st.markdown("<h2 style='margin-bottom: 0;'>TROUBLESHOOTING</h2>", unsafe_allow_html=True)
    
    if 'last_diagnosis' not in st.session_state or not st.session_state['last_diagnosis']:
        st.info("Run a diagnosis first from the Diagnose page.")
        return
        
    diag = st.session_state['last_diagnosis']
    is_demo = st.session_state.get('diagnosis_type', '').endswith("_test")
    cat = str(diag.get("category", "SYSTEM")).upper()
    status = str(diag.get("status", "unknown")).lower()
    
    if is_demo:
        st.warning("OFFLINE DEMO MODE: Simulated Data. No changes will be made to this computer.")
        
    ai = LocalAIEngine()
    
    with st.spinner("AI is analyzing evidence..."):
        ai_result = ai.explain_diagnosis(diag)
        
    is_healthy = status == "healthy" or (not ai_result.get("cannot_fix") and not ai_result.get("repair_id") and status != "problem" and status != "unavailable" and status != "unknown")
    
    prob = ai_result.get("summary", "Unknown Problem")
    
    if status == "unavailable":
        box_color = "#ef4444" # Red
        box_title = f"⚠ DIAGNOSTIC UNAVAILABLE"
    elif status == "unknown":
        box_color = "#f59e0b" # Amber
        box_title = f"⚠ {cat} STATUS UNKNOWN"
    elif is_healthy:
        box_color = "#10b981" # Green
        box_title = f"✓ {cat} HEALTHY"
    else:
        box_color = "#f59e0b" # Amber
        box_title = f"⚠ {cat} PROBLEM"
        
    st.markdown(f"""
        <div style="background: #2a2a2a; border-left: 4px solid {box_color}; padding: 20px; border-radius: 8px; margin-top: 15px;">
            <div style="color: {box_color}; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">{box_title}</div>
            <div style="font-size: 1.1rem;">{prob}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><h4 style='color: #a1a1aa;'>WHAT FIXIT AI FOUND</h4>", unsafe_allow_html=True)
    for ev in ai_result.get("evidence", []):
        st.markdown(f"✓ {ev}")
        
    # AI Analysis Box
    causes = "\n\n".join(ai_result.get("likely_causes", []))
    if status == "unavailable":
        ai_analysis_card("Diagnostic module has not been implemented for this subsystem.")
    elif causes and causes != "None":
        ai_analysis_card(causes)
    elif is_healthy:
        ai_analysis_card(f"All system checks passed for {cat}. No anomalies detected.")
    else:
        ai_analysis_card("INSUFFICIENT_EVIDENCE: No specific software cause could be isolated based on current facts. Hardware issue possible.")
    
    if ai_result.get("cannot_fix") or status == "unavailable" or status == "unknown":
        st.markdown(f"""
            <div style="background: #2a2a2a; border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px; margin-top: 15px;">
                <div style="color: #ef4444; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">SERVICE REQUIRED</div>
                <div style="font-size: 1.1rem; margin-bottom: 10px;">Software diagnostics cannot safely repair this issue.</div>
                <div style="color: #a1a1aa;">Recommended next step: Check hardware connections, privacy settings, or contact an authorized service center.</div>
            </div>
        """, unsafe_allow_html=True)
        return
        
    repair_id = ai_result.get("repair_id")
    if not repair_id:
        st.markdown(f"""
            <div style="background: #2a2a2a; border-left: 4px solid #10b981; padding: 20px; border-radius: 8px; margin-top: 15px;">
                <div style="color: #10b981; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">RESOLVED</div>
                <div style="font-size: 1.1rem;">No repairs recommended. System looks healthy.</div>
            </div>
        """, unsafe_allow_html=True)
        return
        
    engine = RepairEngine()
    repair_info = engine.repairs.get(repair_id)
    
    if not repair_info:
        st.error(f"Unknown repair ID recommended by AI: {repair_id}. Falling back to safe state.")
        return
        
    st.markdown("<br><h4 style='color: #a1a1aa;'>RECOMMENDED FIX</h4>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="repair-box">
            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">{repair_info['name']}</div>
            <div style="margin-bottom: 10px; color: #d1d5db;">{ai_result.get("repair_reason", repair_info['description'])}</div>
            <div style="margin-bottom: 15px;">
                <span style="background: #374151; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">Risk: {repair_info['risk'].upper()}</span>
            </div>
            <div style="color: #9ca3af; font-size: 0.9rem;">
                <strong>Why this is safe:</strong> This only executes pre-approved scripts and does not remove your drivers or delete any personal data.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("FIX THIS PROBLEM", type="primary", use_container_width=True):
            st.session_state['verifying_repair'] = True
            st.session_state['active_repair'] = repair_id
            st.rerun()
            
    with st.expander("View technical details"):
        st.json(diag)
            
    if st.session_state.get('verifying_repair'):
        st.markdown("---")
        st.markdown("<h4 style='color: #a1a1aa;'>FIXIT AI IS WORKING</h4>", unsafe_allow_html=True)
        
        ph = st.empty()
        ph.markdown("✓ Diagnosing device<br>○ Applying repair<br>○ Verifying result", unsafe_allow_html=True)
        time.sleep(1)
        
        active_id = st.session_state['active_repair']
        
        if is_demo:
            ph.markdown("✓ Diagnosing device<br>✓ Applying repair<br>○ Verifying result", unsafe_allow_html=True)
            time.sleep(1)
            success = True
            msg = "Demo Execution Success"
        else:
            success, msg = engine.execute_repair(active_id)
            ph.markdown("✓ Diagnosing device<br>✓ Applying repair<br>○ Verifying result", unsafe_allow_html=True)
            
        time.sleep(1)
        
        if not success:
            st.markdown(f"""
                <div style="background: #2a2a2a; border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px; margin-top: 15px;">
                    <div style="color: #ef4444; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">⚠ REPAIR FAILED</div>
                    <div style="font-size: 1.1rem;">{msg}</div>
                </div>
            """, unsafe_allow_html=True)
            st.session_state['verifying_repair'] = False
            return
            
        if is_demo:
            ph.markdown("✓ Diagnosing device<br>✓ Applying repair<br>✓ Verifying result", unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background: #2a2a2a; border-left: 4px solid #10b981; padding: 20px; border-radius: 8px; margin-top: 15px;">
                    <div style="color: #10b981; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">✓ PROBLEM RESOLVED</div>
                    <div style="font-size: 1.1rem;">Problem has been resolved. (Demo)</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            is_fixed = engine.verify_repair(active_id)
            if is_fixed:
                ph.markdown("✓ Diagnosing device<br>✓ Applying repair<br>✓ Verifying result", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="background: #2a2a2a; border-left: 4px solid #10b981; padding: 20px; border-radius: 8px; margin-top: 15px;">
                        <div style="color: #10b981; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">✓ PROBLEM RESOLVED</div>
                        <div style="font-size: 1.1rem;">Problem has been successfully resolved.</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                ph.markdown("✓ Diagnosing device<br>✓ Applying repair<br>⚠ Verifying result", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="background: #2a2a2a; border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px; margin-top: 15px;">
                        <div style="color: #ef4444; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">⚠ REPAIR FAILED</div>
                        <div style="font-size: 1.1rem;">Issue still persists after repair verification. VERIFICATION INCONCLUSIVE.</div>
                    </div>
                """, unsafe_allow_html=True)
            
        st.session_state['verifying_repair'] = False
