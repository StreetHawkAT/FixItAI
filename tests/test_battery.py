import pytest
from unittest.mock import patch
from diagnostics.battery import check_battery

@patch('diagnostics.battery.run_ps')
def test_battery_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"Bat","EstimatedChargeRemaining":100,"BatteryStatus":2}]'
    res = check_battery()
    assert res["status"] == "healthy"
