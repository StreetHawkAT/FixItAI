import pytest
from unittest.mock import patch
from diagnostics.input_devices import check_input

@patch('diagnostics.input_devices.run_ps')
def test_input_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"Mouse","Status":"OK"}]'
    res = check_input()
    assert res["status"] == "healthy"
