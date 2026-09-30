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
        # flush_dns verify is just lambda: True
        assert engine.verify_repair("flush_dns") == RepairState.VERIFIED_FIXED
        
        # let's mock an actual cmd verification
        mock_run_cmd.return_value = {"exit_code": 0, "stdout": "Running", "stderr": ""}
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
