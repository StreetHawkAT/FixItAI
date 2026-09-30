import pytest
from unittest.mock import patch
from diagnostics.camera import check_camera

@patch('diagnostics.camera.run_ps')
def test_camera_detected(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"Integrated Camera","Status":"OK","Present":true}]'
    res = check_camera()
    assert res["status"] == "healthy"
    assert res["camera_present"] == True
    assert res["camera_enabled"] == True

@patch('diagnostics.camera.run_ps')
def test_camera_disabled(mock_run_ps):
    # PnP device usually shows 'Error' when disabled via Device Manager
    mock_run_ps.return_value = '[{"Name":"Integrated Camera","Status":"Error","Present":true}]'
    res = check_camera()
    assert res["status"] == "problem"
    assert res["camera_present"] == True
    assert res["driver_status"] == "error"
    
@patch('diagnostics.camera.run_ps')
def test_camera_missing(mock_run_ps):
    mock_run_ps.return_value = '[]'
    res = check_camera()
    assert res["status"] == "problem"
    assert res["camera_present"] == False
