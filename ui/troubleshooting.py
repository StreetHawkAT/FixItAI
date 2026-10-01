import streamlit as st
import time
from core.repair_engine import RepairEngine, RepairState
from core.ai_engine import LocalAIEngine

def render_troubleshooting():
    if st.button("← Back to Diagnostics"):
        st.session_state["nav_page"] = "Diagnose"
        st.rerun()

    st.header("TROUBLESHOOTING")
    
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
    
    with st.spinner("FixIt AI is analyzing telemetry..."):
        ai_result = ai.explain_diagnosis(diag)

    action_type = ai_result.get("action_type", "user_action")
    repair_id = ai_result.get("repair_id")
    is_healthy = status == "healthy" or action_type == "none" or (not ai_result.get("cannot_fix") and not repair_id and status != "problem" and status != "unavailable" and status != "unknown")

    prob = ai_result.get("problem") or ai_result.get("summary", "Subsystem Issue Detected")
    confidence = str(ai_result.get("confidence", "MEDIUM")).upper()

    # Determine Header styling
    if status == "unavailable":
        box_title = "⚠ DIAGNOSTIC UNAVAILABLE"
    elif status == "unknown":
        box_title = f"⚠ {cat} STATUS UNKNOWN"
    elif is_healthy:
        box_title = f"✓ {cat} HEALTHY"
    elif action_type == "automated_repair":
        box_title = f"⚡ {cat} - SAFE AUTOMATED FIX AVAILABLE"
    elif action_type == "escalation":
        box_title = f"⚠ {cat} - HARDWARE ESCALATION"
    else:
        box_title = f"⚠ {cat} - USER ACTION REQUIRED"

    # Main Problem Card
    with st.container(border=True):
        st.caption(box_title)
        st.subheader(prob)

    # Telemetry Evidence
    st.markdown("#### WHAT FIXIT AI FOUND")
    evidence_items = ai_result.get("evidence", [])
    if evidence_items:
        for ev in evidence_items:
            st.markdown(f"✓ {ev}")
    else:
        st.caption("No telemetry evidence entries returned.")

    # FixIt AI Analysis (Likely Cause, Confidence, Why)
    st.markdown("#### FIXIT AI ANALYSIS")
    with st.container(border=True):
        col_hdr, col_conf = st.columns([3, 1])
        with col_hdr:
            st.markdown("**LIKELY CAUSE**")
        with col_conf:
            st.markdown(f"**Confidence:** `{confidence}`")

        causes = ai_result.get("likely_causes", [])
        why = ai_result.get("why", "")

        if causes:
            for c in causes:
                st.markdown(f"• {c}")
        elif is_healthy:
            st.markdown(f"All system checks passed for **{cat}**. No anomalies detected.")
        else:
            st.markdown("System telemetry indicates a problem, but root cause could not be confirmed without further testing.")

        if why:
            st.markdown("---")
            st.markdown(f"**Why FixIt AI Thinks This:**\n\n{why}")

    # Subsystem Action Section
    engine = RepairEngine()
    
    # Path A: SAFE AUTOMATED REPAIR AVAILABLE
    if action_type == "automated_repair" and repair_id and not st.session_state.get('verifying_repair'):
        repair_info = engine.repairs.get(repair_id)
        if repair_info:
            st.markdown("#### RECOMMENDED SAFE FIX")
            
            verification_plan = ai_result.get("verification_plan", f"FixIt AI will verify whether Windows reports the {cat} subsystem as healthy.")
            fallback_action = ai_result.get("fallback_action", "Check Windows Device Manager or restart your PC.")
            repair_name = repair_info['name']
            repair_risk = repair_info['risk'].upper()
            repair_desc = ai_result.get("repair_reason", repair_info['description'])
            
            with st.container(border=True):
                col_name, col_risk = st.columns([3, 1])
                with col_name:
                    st.subheader(repair_name)
                with col_risk:
                    st.markdown(f"**Risk:** `{repair_risk}`")

                st.markdown(repair_desc)
                st.markdown("---")
                st.markdown("**Why this is safe:** This only executes a pre-approved Windows diagnostic command from our strict allowlist. It does not delete personal files or modify registry keys.")
                st.markdown(f"**Verification Plan:** {verification_plan}")
                st.markdown(f"**If the fix doesn't work:** {fallback_action}")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("RUN SAFE REPAIR", type="primary", use_container_width=True):
                    st.session_state['verifying_repair'] = True
                    st.session_state['active_repair'] = repair_id
                    st.rerun()

            with st.expander("View technical telemetry details"):
                st.json(diag)
            return

    # Path B: ADDITIONAL USER ACTION REQUIRED
    elif action_type == "user_action":
        st.markdown("#### RECOMMENDED NEXT STEPS")
        rec_action = ai_result.get("recommended_action", "Follow the troubleshooting steps below.")
        user_steps = ai_result.get("user_steps", [])
        fallback_action = ai_result.get("fallback_action", "")

        with st.container(border=True):
            st.subheader("Action Required")
            st.markdown(rec_action)
            st.warning("**Automated Fix:** Not available — Telemetry does not identify a safe automated script. Targeted manual troubleshooting is required.")
            
            if user_steps:
                st.markdown("**Recommended Troubleshooting Steps:**")
                for s in user_steps:
                    st.markdown(f"- {s}")
            if fallback_action:
                st.markdown("---")
                st.markdown(f"**When service / escalation is justified:** {fallback_action}")

        with st.expander("View technical telemetry details"):
            st.json(diag)
        return

    # Path C: SERVICE / HARDWARE ESCALATION
    elif action_type == "escalation":
        st.markdown("#### HARDWARE ESCALATION")
        rec_action = ai_result.get("recommended_action", "Hardware investigation is justified.")
        fallback_action = ai_result.get("fallback_action", "")

        with st.container(border=True):
            st.error("### Hardware / Manufacturer Service Justified")
            st.markdown(rec_action)
            if fallback_action:
                st.markdown(fallback_action)

        with st.expander("View technical telemetry details"):
            st.json(diag)
        return

    # Path D: SYSTEM HEALTHY
    elif is_healthy:
        with st.container(border=True):
            st.success(f"### ✓ SYSTEM HEALTHY\n\nAll diagnostic checks for the **{cat}** subsystem passed with no active errors detected.")
        
        with st.expander("View technical telemetry details"):
            st.json(diag)
        return

    # Execution & Verification Phase
    if st.session_state.get('verifying_repair'):
        st.markdown("---")
        st.subheader("FIXIT AI IS WORKING")
        
        ph = st.empty()
        ph.markdown("**✓ Diagnosing device**  \n○ Applying repair  \n○ Verifying result")
        time.sleep(1)
        
        active_id = st.session_state['active_repair']
        
        if is_demo:
            ph.markdown("**✓ Diagnosing device**  \n**✓ Applying repair**  \n○ Verifying result")
            time.sleep(1)
            
            ph.markdown("**✓ Diagnosing device**  \n**✓ Applying repair**  \n**✓ Verifying result**")
            with st.container(border=True):
                st.success("### ✓ PROBLEM RESOLVED\n\nRepair verified successfully in Offline Demo Mode.")
            if st.button("Done", key="demo_done"):
                st.session_state['verifying_repair'] = False
                st.rerun()
            return
            
        result = engine.execute_repair(active_id, diagnostic_id=diag.get("id", "unknown"))
        
        if result["state"] == RepairState.REQUIRES_ADMIN:
            with st.container(border=True):
                st.warning("### ⚠ ELEVATION REQUIRED")
                st.markdown(f"**{result['msg']}**")
                st.info("Please close FixIt AI, right-click, and select 'Run as administrator'.")
            if st.button("Cancel"):
                st.session_state['verifying_repair'] = False
                st.rerun()
            return

        if result["state"] == RepairState.FAILED:
            ph.markdown("**✓ Diagnosing device**  \n**⚠ Applying repair**  \n○ Verifying result")
            details = result.get('details', {})
            err_msg = details.get('stderr', '') or details.get('exception', '')
            with st.container(border=True):
                st.error("### ⚠ REPAIR EXECUTION FAILED")
                st.markdown(f"{result['msg']}")
                if err_msg:
                    st.code(err_msg)
            if st.button("Done", key="fail_done"):
                st.session_state['verifying_repair'] = False
                st.rerun()
            return
            
        ph.markdown("**✓ Diagnosing device**  \n**✓ Applying repair**  \n○ Verifying result")
        time.sleep(1)
        
        verify_state = engine.verify_repair(active_id)
        if verify_state == RepairState.VERIFIED_FIXED:
            ph.markdown("**✓ Diagnosing device**  \n**✓ Applying repair**  \n**✓ Verifying result**")
            msg = "Camera device was successfully re-enabled and Windows now reports it as operational." if active_id == "enable_camera" else "Repair executed successfully and system verification confirmed the issue is resolved."
            with st.container(border=True):
                st.success(f"### ✓ REPAIR VERIFIED FIXED\n\n{msg}")
                if hasattr(engine, 'last_verification_details') and engine.last_verification_details:
                    evidence_list = engine.last_verification_details.get("evidence", [])
                    if evidence_list:
                        st.markdown("**Verification Evidence:**")
                        for ev in evidence_list:
                            st.markdown(f"✓ {ev}")
        elif verify_state == RepairState.EXECUTED_NOT_FIXED:
            ph.markdown("**✓ Diagnosing device**  \n**✓ Applying repair**  \n**⚠ Verifying result**")
            fallback_action = ai_result.get("fallback_action", "Try manual troubleshooting or contact support.")
            user_steps = ai_result.get("user_steps", [])
            with st.container(border=True):
                st.warning("### ⚠ REPAIR EXECUTED, BUT PROBLEM PERSISTS\n\nThe automated repair command executed without error, but post-repair verification detected that the underlying issue was not resolved.")
                if hasattr(engine, 'last_verification_details') and engine.last_verification_details:
                    evidence_list = engine.last_verification_details.get("evidence", [])
                    if evidence_list:
                        st.markdown("**Verification Evidence:**")
                        for ev in evidence_list:
                            st.markdown(f"• {ev}")
                if user_steps:
                    st.markdown("**Next Recommended Actions:**")
                    for s in user_steps:
                        st.markdown(f"- {s}")
                st.markdown(f"**Escalation:** {fallback_action}")
        else:
            ph.markdown("**✓ Diagnosing device**  \n**✓ Applying repair**  \n**⚠ Verification error**")
            with st.container(border=True):
                st.error("### ⚠ VERIFICATION COULD NOT COMPLETE\n\nThe repair command was executed, but the verification procedure encountered an unexpected error.")
                if getattr(engine, 'last_verification_error', None):
                    st.caption(f"Verification error: {engine.last_verification_error}")
                st.info("Please test the device manually to verify if functionality has returned.")
            
        with st.expander("View execution details"):
            exec_details = {
                "execution": result.get("details", {}),
                "verification": getattr(engine, "last_verification_details", None)
            }
            st.json(exec_details)
            
        if st.button("Done", key="finish_done"):
            st.session_state['verifying_repair'] = False
            st.rerun()
