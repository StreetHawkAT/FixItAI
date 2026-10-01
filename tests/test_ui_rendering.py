import pytest
from unittest.mock import patch, MagicMock
import streamlit as st

def test_recommended_safe_fix_renders_plain_markdown_no_raw_html():
    """Verify that the Recommended Safe Fix section renders via native Streamlit widgets without any raw HTML tags."""
    diag_data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": False,
        "device_status": "disabled",
        "disabled_cameras": ["Integrated Camera"],
        "devices": [{"Name": "Integrated Camera", "Status": "Error", "Problem": 22}],
        "evidence": ["Device: Integrated Camera | Status: Error | PnP Code: 22"]
    }
    
    with patch.dict(st.session_state, {
        "last_diagnosis": diag_data,
        "diagnosis_type": "camera_test",
        "verifying_repair": False
    }, clear=True):
        with patch("streamlit.markdown") as mock_markdown, \
             patch("streamlit.info") as mock_info, \
             patch("streamlit.subheader") as mock_subhdr, \
             patch("streamlit.button", return_value=False), \
             patch("streamlit.container") as mock_container, \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock()]), \
             patch("streamlit.expander"), \
             patch("streamlit.warning"), \
             patch("streamlit.caption"), \
             patch("streamlit.header"), \
             patch("streamlit.spinner"):
            
            from ui.troubleshooting import render_troubleshooting
            render_troubleshooting()
            
            # Collect all strings passed to markdown, info, subheader
            all_rendered_strings = []
            for call in mock_markdown.call_args_list:
                if call.args:
                    all_rendered_strings.append(str(call.args[0]))
            for call in mock_info.call_args_list:
                if call.args:
                    all_rendered_strings.append(str(call.args[0]))
            for call in mock_subhdr.call_args_list:
                if call.args:
                    all_rendered_strings.append(str(call.args[0]))
                    
            combined_text = "\n".join(all_rendered_strings)
            
            # Required elements must be present
            assert "Why this is safe:" in combined_text
            assert "Verification Plan:" in combined_text
            assert "If the fix doesn't work:" in combined_text
            
            # Raw HTML tags must NEVER be passed to the UI in this section
            assert "<div" not in combined_text, f"Found <div in output: {combined_text}"
            assert "</div>" not in combined_text, f"Found </div> in output: {combined_text}"
            assert "<strong" not in combined_text, f"Found <strong in output: {combined_text}"
            assert "</strong>" not in combined_text, f"Found </strong> in output: {combined_text}"
            assert "style=" not in combined_text, f"Found style= in output: {combined_text}"

def test_user_action_renders_plain_markdown():
    """Verify that User Action required section renders without HTML tags."""
    diag_data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": False,
        "driver_status": "error",
        "device_status": "error",
        "devices": [{"Name": "HD Webcam", "Status": "Error", "Problem": 10}],
        "evidence": ["Device: HD Webcam | Status: Error | PnP Code: 10"]
    }
    
    with patch.dict(st.session_state, {
        "last_diagnosis": diag_data,
        "diagnosis_type": "camera_test",
        "verifying_repair": False
    }, clear=True):
        with patch("streamlit.markdown") as mock_markdown, \
             patch("streamlit.info"), \
             patch("streamlit.subheader"), \
             patch("streamlit.button", return_value=False), \
             patch("streamlit.container"), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock()]), \
             patch("streamlit.expander"), \
             patch("streamlit.warning") as mock_warn, \
             patch("streamlit.caption"), \
             patch("streamlit.header"), \
             patch("streamlit.spinner"):
            
            from ui.troubleshooting import render_troubleshooting
            render_troubleshooting()
            
            all_rendered_strings = [str(call.args[0]) for call in mock_markdown.call_args_list if call.args]
            all_rendered_strings += [str(call.args[0]) for call in mock_warn.call_args_list if call.args]
            combined = "\n".join(all_rendered_strings)
            
            assert "<div" not in combined
            assert "style=" not in combined

def test_apptest_camera_code22_recommended_safe_fix_no_html_tags():
    """End-to-end Streamlit AppTest ensuring Camera Code 22 scenario displays clean text without HTML markup."""
    import os
    from streamlit.testing.v1 import AppTest
    
    app_path = os.path.abspath("app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run(timeout=30)
    
    # Inject camera Code 22 diagnosis
    at.session_state['last_diagnosis'] = {
        'category': 'camera', 'status': 'problem',
        'camera_present': True, 'camera_enabled': False,
        'driver_status': 'ok', 'device_status': 'disabled',
        'total_cameras': 1, 'disabled_cameras': ['Integrated Camera'],
        'devices': [
            {'Name': 'Integrated Camera', 'Status': 'Error', 'Present': True, 'Problem': 22, 'ProblemDescription': 'This device is disabled. (Code 22).'}
        ],
        'frame_server_service': 'Running', 'privacy_access': 'Allow',
        'evidence': [
            'Detected 1 camera/imaging device(s).',
            'Device: Integrated Camera | Status: Error | PnP Code: 22 (This device is disabled. (Code 22).)',
            'Windows Camera Frame Server service: Running',
            'Windows Camera Privacy setting: Allow'
        ]
    }
    at.session_state['diagnosis_type'] = 'demo_test'
    at.session_state['nav_page'] = 'Troubleshoot'
    at.run(timeout=30)
    
    troubleshoot_elements = []
    for elem in at.main:
        val = getattr(elem, 'value', '')
        if val:
            troubleshoot_elements.append(str(val))
    
    full_output = '\n'.join(troubleshoot_elements)
    
    assert "RECOMMENDED SAFE FIX" in full_output
    rec_fix_text = full_output.split("RECOMMENDED SAFE FIX")[1]
    
    # Assert expected plain text is present
    assert "Why this is safe:" in rec_fix_text
    assert "Verification Plan:" in rec_fix_text
    assert "If the fix doesn't work:" in rec_fix_text
    
    # Assert NO HTML tags or attributes are rendered as text or literal code blocks
    assert "<div" not in rec_fix_text, f"Found raw '<div' in UI output: {rec_fix_text}"
    assert "</div>" not in rec_fix_text, f"Found raw '</div>' in UI output: {rec_fix_text}"
    assert "<strong" not in rec_fix_text, f"Found raw '<strong' in UI output: {rec_fix_text}"
    assert "</strong>" not in rec_fix_text, f"Found raw '</strong>' in UI output: {rec_fix_text}"
    assert "style=" not in rec_fix_text, f"Found raw 'style=' in UI output: {rec_fix_text}"

def test_troubleshooting_repair_verified_fixed_rendering():
    """Verify that when a real repair is verified fixed, the UI renders clean text and evidence."""
    diag_data = {
        "category": "camera",
        "status": "problem",
        "camera_present": True,
        "camera_enabled": False,
        "device_status": "disabled",
        "disabled_cameras": ["ASUS FHD webcam"],
        "devices": [{"Name": "ASUS FHD webcam", "Status": "Error", "Problem": 22}],
        "evidence": ["Device: ASUS FHD webcam | Status: Error | PnP Code: 22"]
    }
    
    with patch.dict(st.session_state, {
        "last_diagnosis": diag_data,
        "diagnosis_type": "camera_real",
        "verifying_repair": True,
        "active_repair": "enable_camera"
    }, clear=True):
        with patch("core.repair_engine.RepairEngine.execute_repair", return_value={"state": "EXECUTED", "msg": "Success", "details": {}}), \
             patch("core.repair_engine.RepairEngine.verify_repair", return_value="VERIFIED_FIXED"), \
             patch("streamlit.markdown") as mock_markdown, \
             patch("streamlit.success") as mock_success, \
             patch("streamlit.button", return_value=False), \
             patch("streamlit.container"), \
             patch("streamlit.subheader"), \
             patch("streamlit.empty"), \
             patch("streamlit.expander"), \
             patch("streamlit.header"), \
             patch("time.sleep"):
             
            from ui.troubleshooting import render_troubleshooting
            render_troubleshooting()
            
            # Check success message
            success_calls = [str(call.args[0]) for call in mock_success.call_args_list if call.args]
            assert any("REPAIR VERIFIED FIXED" in s for s in success_calls)
            assert any("Camera device was successfully re-enabled" in s for s in success_calls)


