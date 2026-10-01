import pytest
import subprocess
from unittest.mock import patch, MagicMock
from core.repair_engine import RepairEngine, RepairState, run_cmd

@pytest.fixture
def engine():
    return RepairEngine()

def test_run_cmd_success():
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = "Success output"
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        result = run_cmd("echo 'test'")
        
        assert result["exit_code"] == 0
        assert result["stdout"] == "Success output"
        assert not result["timeout"]
        assert result["exception"] is None

def test_run_cmd_timeout():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30, output=b"partial", stderr=b"")
        
        result = run_cmd("sleep 100")
        
        assert result["timeout"] is True
        assert result["stdout"] == "partial"
        assert result["exit_code"] == -1

def test_execute_repair_invalid_id(engine):
    result = engine.execute_repair("invalid_repair_id")
    assert result["state"] == RepairState.FAILED
    assert "not found" in result["msg"]

@patch('core.repair_engine.is_admin', return_value=False)
def test_execute_repair_requires_admin_not_elevated(mock_is_admin, engine):
    # restart_wlan requires admin
    result = engine.execute_repair("restart_wlan")
    assert result["state"] == RepairState.REQUIRES_ADMIN

@patch('core.repair_engine.is_admin', return_value=True)
def test_execute_repair_requires_admin_elevated_success(mock_is_admin, engine):
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "exception": None,
            "end_time": "2024-01-01T00:00:00"
        }
        result = engine.execute_repair("restart_wlan")
        assert result["state"] == RepairState.EXECUTED

def test_execute_repair_failure_exit_code(engine):
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {
            "exit_code": 1,
            "stdout": "",
            "stderr": "Access denied",
            "timeout": False,
            "exception": None,
            "end_time": "2024-01-01T00:00:00"
        }
        result = engine.execute_repair("flush_dns") # flush_dns does not require admin
        assert result["state"] == RepairState.FAILED
        assert "Non-zero exit code: 1" in result["msg"] or "Exit code: 1" in result["msg"]

def test_verify_repair_success(engine):
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": "Running", "stderr": ""}
        assert engine.verify_repair("flush_dns") == RepairState.VERIFIED_FIXED
        assert engine.verify_repair("restart_wlan") == RepairState.VERIFIED_FIXED

def test_verify_repair_failure(engine):
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": "Stopped", "stderr": ""}
        assert engine.verify_repair("restart_wlan") == RepairState.EXECUTED_NOT_FIXED

def test_verify_repair_error(engine):
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 1, "stdout": "", "stderr": "Command not found"}
        assert engine.verify_repair("restart_wlan") == RepairState.VERIFICATION_FAILED

def test_run_verify_cmd_ps5_compat():
    from core.repair_engine import run_verify_cmd
    
    # Test boolean output true (simulating Test-Connection -Quiet success)
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": "True\r\n", "stderr": ""}
        assert run_verify_cmd("dummy_cmd", is_bool=True) is True
        
    # Test boolean output false (simulating Test-Connection -Quiet timeout/fail)
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": "False\r\n", "stderr": ""}
        assert run_verify_cmd("dummy_cmd", is_bool=True) is False
        
    # Test error output
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 1, "stdout": "", "stderr": "Error"}
        try:
            run_verify_cmd("dummy_cmd", is_bool=True)
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Verification command failed" in str(e)

def test_camera_verification_code22_to_code0_verified_fixed(engine):
    """1. Camera Code 22 -> enable_camera -> repair succeeds -> post-repair camera reports Code 0 -> VERIFIED_FIXED"""
    import json
    post_repair_output = json.dumps([
        {"Name": "Integrated Camera", "Status": "OK", "Problem": 0, "ProblemDescription": "This device is working properly."}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": post_repair_output, "stderr": ""}
        assert engine.verify_repair("enable_camera") == RepairState.VERIFIED_FIXED
        assert engine.last_verification_details is not None
        assert "Integrated Camera" in engine.last_verification_details["healthy_devices"]
        assert len(engine.last_verification_details["problem_devices"]) == 0

def test_camera_verification_code22_remains_executed_not_fixed(engine):
    """2. Camera Code 22 -> repair command succeeds -> camera remains Code 22 -> EXECUTED_NOT_FIXED"""
    import json
    post_repair_output = json.dumps([
        {"Name": "Integrated Camera", "Status": "Error", "Problem": 22, "ProblemDescription": "This device is disabled. (Code 22)."}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": post_repair_output, "stderr": ""}
        assert engine.verify_repair("enable_camera") == RepairState.EXECUTED_NOT_FIXED
        assert len(engine.last_verification_details["problem_devices"]) == 1

def test_camera_verification_command_exception_verification_failed(engine):
    """3. Camera verification command itself throws an exception -> VERIFICATION_FAILED"""
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 1, "stdout": "", "stderr": "CimJobException: No Win32_PnPEntity objects found"}
        assert engine.verify_repair("enable_camera") == RepairState.VERIFICATION_FAILED
        assert "Verification command failed with exit code 1" in engine.last_verification_error

    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": "", "stderr": "", "timeout": True}
        assert engine.verify_repair("enable_camera") == RepairState.VERIFICATION_FAILED
        assert "timed out" in engine.last_verification_error

def test_camera_verification_multiple_cameras(engine):
    """4. Multiple cameras:
       - IR camera Code 0 + FHD webcam Code 22 -> EXECUTED_NOT_FIXED (IR must not hide failed FHD)
       - IR camera Code 0 + FHD webcam Code 0 -> VERIFIED_FIXED
    """
    import json
    
    # Sub-case A: IR camera OK (0), but FHD webcam still Error (22)
    partial_output = json.dumps([
        {"Name": "ASUS IR camera", "Status": "OK", "Problem": 0, "ProblemDescription": "This device is working properly."},
        {"Name": "ASUS FHD webcam", "Status": "Error", "Problem": 22, "ProblemDescription": "This device is disabled. (Code 22)."}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": partial_output, "stderr": ""}
        assert engine.verify_repair("enable_camera") == RepairState.EXECUTED_NOT_FIXED
        assert "ASUS IR camera" in engine.last_verification_details["healthy_devices"]
        assert any(p["name"] == "ASUS FHD webcam" for p in engine.last_verification_details["problem_devices"])

    # Sub-case B: Both IR camera and FHD webcam report OK (0)
    full_output = json.dumps([
        {"Name": "ASUS IR camera", "Status": "OK", "Problem": 0, "ProblemDescription": "This device is working properly."},
        {"Name": "ASUS FHD webcam", "Status": "OK", "Problem": 0, "ProblemDescription": "This device is working properly."}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run_cmd:
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": full_output, "stderr": ""}
        assert engine.verify_repair("enable_camera") == RepairState.VERIFIED_FIXED
        assert "ASUS IR camera" in engine.last_verification_details["healthy_devices"]
        assert "ASUS FHD webcam" in engine.last_verification_details["healthy_devices"]
        assert len(engine.last_verification_details["problem_devices"]) == 0

def test_enable_wifi_verification(engine):
    """Regression test enable_wifi:
       1. Adapter enabled -> VERIFIED_FIXED
       2. Adapter disabled -> EXECUTED_NOT_FIXED
       3. No adapter found -> EXECUTED_NOT_FIXED
       4. Command error -> VERIFICATION_FAILED
    """
    import json
    # 1. Success
    adapter_ok = json.dumps([
        {"Name": "Wi-Fi", "InterfaceDescription": "Realtek 8852CE WiFi 6E", "Status": "Up", "AdminStatus": 1}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": adapter_ok, "stderr": ""}
        assert engine.verify_repair("enable_wifi") == RepairState.VERIFIED_FIXED
        assert "is enabled" in engine.last_verification_details["evidence"][0]

    # 2. Problem remains: disabled
    adapter_disabled = json.dumps([
        {"Name": "Wi-Fi", "InterfaceDescription": "Realtek 8852CE WiFi 6E", "Status": "Disabled", "AdminStatus": 2}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": adapter_disabled, "stderr": ""}
        assert engine.verify_repair("enable_wifi") == RepairState.EXECUTED_NOT_FIXED
        assert "is disabled" in engine.last_verification_details["evidence"][0]

    # 3. No Wi-Fi adapter found
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": "[]", "stderr": ""}
        assert engine.verify_repair("enable_wifi") == RepairState.EXECUTED_NOT_FIXED

    # 4. Command fails
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 1, "stdout": "", "stderr": "Access denied"}
        assert engine.verify_repair("enable_wifi") == RepairState.VERIFICATION_FAILED

def test_ip_renew_verification(engine):
    """Regression test ip_renew:
       1. Valid DHCP IP (not APIPA) -> VERIFIED_FIXED
       2. APIPA 169.254.x.x -> EXECUTED_NOT_FIXED
       3. Empty / no IP -> EXECUTED_NOT_FIXED
       4. Command error / timeout -> VERIFICATION_FAILED
       5. Wi-Fi invalid (APIPA) + Ethernet valid -> EXECUTED_NOT_FIXED (Targeting regression test)
       6. Relevant adapter valid + Ethernet invalid -> VERIFIED_FIXED
    """
    import json
    # 1. Success with valid IP
    ip_ok = json.dumps([
        {"InterfaceAlias": "Wi-Fi", "IPAddress": "192.168.1.100", "PrefixOrigin": 3}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": ip_ok, "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.VERIFIED_FIXED
        assert "valid IPv4 address" in engine.last_verification_details["evidence"][0]

    # 2. Problem remains: APIPA address
    ip_apipa = json.dumps([
        {"InterfaceAlias": "Wi-Fi", "IPAddress": "169.254.10.20", "PrefixOrigin": 2}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": ip_apipa, "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.EXECUTED_NOT_FIXED
        assert "APIPA address" in engine.last_verification_details["evidence"][0]

    # 3. Empty
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": "[]", "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.EXECUTED_NOT_FIXED

    # 4. Timeout / error
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": "", "stderr": "", "timeout": True}
        assert engine.verify_repair("ip_renew") == RepairState.VERIFICATION_FAILED

    # 5. Targeted regression: Wi-Fi invalid + Ethernet valid -> must NOT produce VERIFIED_FIXED for Wi-Fi repair
    ip_wifi_fail_eth_ok = json.dumps([
        {"InterfaceAlias": "Wi-Fi", "IPAddress": "169.254.10.20", "PrefixOrigin": 2},
        {"InterfaceAlias": "Ethernet", "IPAddress": "192.168.1.50", "PrefixOrigin": 3}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": ip_wifi_fail_eth_ok, "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.EXECUTED_NOT_FIXED
        # Verify evidence specifically called out target adapter failure and ignored unrelated interface
        evidence = engine.last_verification_details["evidence"]
        assert any("Target adapter 'Wi-Fi' has APIPA address" in ev for ev in evidence)
        assert any("Unrelated interface 'Ethernet' has IP 192.168.1.50 (ignored for Wi-Fi repair)" in ev for ev in evidence)

    # 6. Targeted regression: Relevant adapter valid + Ethernet invalid -> VERIFIED_FIXED
    ip_wifi_ok_eth_fail = json.dumps([
        {"InterfaceAlias": "Wi-Fi", "IPAddress": "192.168.1.50", "PrefixOrigin": 3},
        {"InterfaceAlias": "Ethernet", "IPAddress": "169.254.99.12", "PrefixOrigin": 2}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": ip_wifi_ok_eth_fail, "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.VERIFIED_FIXED
        evidence = engine.last_verification_details["evidence"]
        assert any("Target adapter 'Wi-Fi' has valid IPv4 address: 192.168.1.50" in ev for ev in evidence)

def test_flush_dns_verification(engine):
    """Regression test flush_dns:
       1. Dnscache running + localhost resolves -> VERIFIED_FIXED
       2. Dnscache stopped -> EXECUTED_NOT_FIXED
       3. Dnscache running + resolution fails -> EXECUTED_NOT_FIXED
       4. Service query fails -> VERIFICATION_FAILED
    """
    import json
    svc_running = json.dumps({"Name": "Dnscache", "Status": 4})
    svc_stopped = json.dumps({"Name": "Dnscache", "Status": 1})
    res_ok = json.dumps({"Name": "localhost", "IPAddress": "127.0.0.1"})

    # 1. Success
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.side_effect = [
            {"exit_code": 0, "stdout": svc_running, "stderr": ""},
            {"exit_code": 0, "stdout": res_ok, "stderr": ""}
        ]
        assert engine.verify_repair("flush_dns") == RepairState.VERIFIED_FIXED
        assert len(engine.last_verification_details["evidence"]) == 2

    # 2. Dnscache stopped
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.side_effect = [
            {"exit_code": 0, "stdout": svc_stopped, "stderr": ""}
        ]
        assert engine.verify_repair("flush_dns") == RepairState.EXECUTED_NOT_FIXED

    # 3. Resolution fails
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.side_effect = [
            {"exit_code": 0, "stdout": svc_running, "stderr": ""},
            {"exit_code": 1, "stdout": "", "stderr": "Could not resolve"}
        ]
        assert engine.verify_repair("flush_dns") == RepairState.EXECUTED_NOT_FIXED

    # 4. Service query exception
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.side_effect = [
            {"exit_code": 1, "stdout": "", "stderr": "RPC server unavailable"}
        ]
        assert engine.verify_repair("flush_dns") == RepairState.VERIFICATION_FAILED

def test_restart_audio_verification(engine):
    """Regression test restart_audio:
       1. AudioSrv + AudioEndpointBuilder running -> VERIFIED_FIXED
       2. AudioSrv stopped -> EXECUTED_NOT_FIXED
       3. Query fails -> VERIFICATION_FAILED
    """
    import json
    audio_ok = json.dumps([
        {"Name": "AudioEndpointBuilder", "Status": 4},
        {"Name": "AudioSrv", "Status": 4}
    ])
    audio_stopped = json.dumps([
        {"Name": "AudioEndpointBuilder", "Status": 4},
        {"Name": "AudioSrv", "Status": 1}
    ])
    # 1. Success
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": audio_ok, "stderr": ""}
        assert engine.verify_repair("restart_audio") == RepairState.VERIFIED_FIXED

    # 2. Stopped
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": audio_stopped, "stderr": ""}
        assert engine.verify_repair("restart_audio") == RepairState.EXECUTED_NOT_FIXED

    # 3. Exception
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 1, "stdout": "", "stderr": "Access denied"}
        assert engine.verify_repair("restart_audio") == RepairState.VERIFICATION_FAILED

def test_restart_bluetooth_verification(engine):
    """Regression test restart_bluetooth:
       1. bthserv running -> VERIFIED_FIXED
       2. bthserv stopped -> EXECUTED_NOT_FIXED
       3. Query error -> VERIFICATION_FAILED
    """
    import json
    bth_ok = json.dumps({"Name": "bthserv", "Status": 4})
    bth_stopped = json.dumps({"Name": "bthserv", "Status": 1})

    # 1. Success
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": bth_ok, "stderr": ""}
        assert engine.verify_repair("restart_bluetooth") == RepairState.VERIFIED_FIXED

    # 2. Stopped
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": bth_stopped, "stderr": ""}
        assert engine.verify_repair("restart_bluetooth") == RepairState.EXECUTED_NOT_FIXED

    # 3. Error
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 1, "stdout": "", "stderr": "Failed"}
        assert engine.verify_repair("restart_bluetooth") == RepairState.VERIFICATION_FAILED

def test_restart_spooler_verification(engine):
    """Regression test restart_spooler:
       1. Spooler running -> VERIFIED_FIXED
       2. Spooler stopped -> EXECUTED_NOT_FIXED
       3. Query error -> VERIFICATION_FAILED
    """
    import json
    spooler_ok = json.dumps({"Name": "Spooler", "Status": 4})
    spooler_stopped = json.dumps({"Name": "Spooler", "Status": 1})

    # 1. Success
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": spooler_ok, "stderr": ""}
        assert engine.verify_repair("restart_spooler") == RepairState.VERIFIED_FIXED

    # 2. Stopped
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": spooler_stopped, "stderr": ""}
        assert engine.verify_repair("restart_spooler") == RepairState.EXECUTED_NOT_FIXED

    # 3. Error
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 1, "stdout": "", "stderr": "Error"}
        assert engine.verify_repair("restart_spooler") == RepairState.VERIFICATION_FAILED

def test_restart_wuauserv_verification(engine):
    """Regression test restart_wuauserv:
       1. wuauserv running -> VERIFIED_FIXED
       2. wuauserv stopped (unspecified metadata) -> EXECUTED_NOT_FIXED
       3. Query error -> VERIFICATION_FAILED
       4. wuauserv stopped but healthy trigger standby (ExitCode 0, StartType Manual) -> VERIFIED_FIXED
       5. wuauserv genuine restart failure (Disabled) -> EXECUTED_NOT_FIXED
       6. wuauserv genuine restart failure (Crashed with ExitCode != 0) -> EXECUTED_NOT_FIXED
    """
    import json
    wu_ok = json.dumps({"Name": "wuauserv", "Status": 4})
    wu_stopped = json.dumps({"Name": "wuauserv", "Status": 1})

    # 1. Success (actively running)
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_ok, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.VERIFIED_FIXED

    # 2. Stopped (legacy mock / unspecified metadata)
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_stopped, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.EXECUTED_NOT_FIXED

    # 3. Error
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 1, "stdout": "", "stderr": "Error"}
        assert engine.verify_repair("restart_wuauserv") == RepairState.VERIFICATION_FAILED

    # 4. Successful restart with appropriate post-restart trigger standby state (Windows 10/11 normal behavior)
    wu_standby = json.dumps({
        "Name": "wuauserv",
        "Status": 1,
        "StartType": 3,
        "ExitCode": 0,
        "StartMode": "Manual"
    })
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_standby, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.VERIFIED_FIXED
        assert "trigger standby" in engine.last_verification_details["evidence"][0]

    # 5. Genuine restart failure: Service is disabled
    wu_disabled = json.dumps({
        "Name": "wuauserv",
        "Status": 1,
        "StartType": 4,
        "ExitCode": 1058,
        "StartMode": "Disabled"
    })
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_disabled, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.EXECUTED_NOT_FIXED
        assert "Disabled" in engine.last_verification_details["evidence"][0]

    # 6. Genuine restart failure: Service crashed or terminated abnormally (non-zero ExitCode)
    wu_crashed = json.dumps({
        "Name": "wuauserv",
        "Status": 1,
        "StartType": 3,
        "ExitCode": 1067,
        "StartMode": "Manual"
    })
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_crashed, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.EXECUTED_NOT_FIXED
        assert "terminated abnormally" in engine.last_verification_details["evidence"][0]

def test_regression_ip_renew_wifi_invalid_ethernet_valid(engine):
    """Regression 1: Wi-Fi invalid (APIPA) + Ethernet valid
       Must NOT produce VERIFIED_FIXED for the Wi-Fi repair.
    """
    import json
    ip_data = json.dumps([
        {"InterfaceAlias": "Wi-Fi", "IPAddress": "169.254.10.20", "PrefixOrigin": 2},
        {"InterfaceAlias": "Ethernet", "IPAddress": "192.168.1.100", "PrefixOrigin": 3}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": ip_data, "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.EXECUTED_NOT_FIXED
        details = engine.last_verification_details
        assert details["target_adapter"] == "Wi-Fi"
        assert any("Target adapter 'Wi-Fi' has APIPA address: 169.254.10.20" in e for e in details["evidence"])
        assert any("Unrelated interface 'Ethernet' has IP 192.168.1.100 (ignored for Wi-Fi repair)" in e for e in details["evidence"])

def test_regression_ip_renew_relevant_adapter_valid(engine):
    """Regression 2: Relevant adapter valid -> VERIFIED_FIXED."""
    import json
    ip_data = json.dumps([
        {"InterfaceAlias": "Wi-Fi", "IPAddress": "192.168.1.55", "PrefixOrigin": 3},
        {"InterfaceAlias": "Ethernet", "IPAddress": "169.254.44.81", "PrefixOrigin": 2}
    ])
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": ip_data, "stderr": ""}
        assert engine.verify_repair("ip_renew") == RepairState.VERIFIED_FIXED
        details = engine.last_verification_details
        assert any("Target adapter 'Wi-Fi' has valid IPv4 address: 192.168.1.55" in e for e in details["evidence"])

def test_regression_wuauserv_trigger_standby_verified_fixed(engine):
    """Regression 3: wuauserv successful restart with appropriate post-restart trigger standby state -> VERIFIED_FIXED."""
    import json
    wu_standby = json.dumps({
        "Name": "wuauserv",
        "Status": 1,
        "StartType": 3,
        "ExitCode": 0,
        "StartMode": "Manual"
    })
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_standby, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.VERIFIED_FIXED
        details = engine.last_verification_details
        assert "trigger standby" in details["evidence"][0]

def test_regression_wuauserv_genuine_restart_failure(engine):
    """Regression 4: wuauserv genuine restart failure -> EXECUTED_NOT_FIXED."""
    import json
    # Case A: Disabled
    wu_disabled = json.dumps({
        "Name": "wuauserv",
        "Status": 1,
        "StartType": 4,
        "ExitCode": 1058,
        "StartMode": "Disabled"
    })
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_disabled, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.EXECUTED_NOT_FIXED
        assert "Disabled" in engine.last_verification_details["evidence"][0]

    # Case B: Crashed / Aborted
    wu_crashed = json.dumps({
        "Name": "wuauserv",
        "Status": 1,
        "StartType": 3,
        "ExitCode": 1067,
        "StartMode": "Manual"
    })
    with patch('core.repair_engine.run_cmd') as mock_run:
        mock_run.return_value = {"exit_code": 0, "stdout": wu_crashed, "stderr": ""}
        assert engine.verify_repair("restart_wuauserv") == RepairState.EXECUTED_NOT_FIXED
        assert "terminated abnormally" in engine.last_verification_details["evidence"][0]




