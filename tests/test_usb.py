import pytest
from unittest.mock import patch
from diagnostics.usb import check_usb

@patch('diagnostics.usb.run_ps')
def test_usb_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"USBHub","Status":"OK"}]'
    res = check_usb()
    assert res["status"] == "healthy"
