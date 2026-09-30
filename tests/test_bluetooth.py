import pytest
from unittest.mock import patch
from diagnostics.bluetooth import check_bluetooth

@patch('diagnostics.bluetooth.run_ps')
def test_bluetooth_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[{"Name":"BT Adapter","Status":"OK"}]']
    res = check_bluetooth()
    assert res["status"] == "healthy"
