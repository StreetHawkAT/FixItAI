import pytest
from unittest.mock import patch
from diagnostics.drivers import check_drivers

@patch('diagnostics.drivers.run_ps')
def test_drivers_healthy(mock_run_ps):
    mock_run_ps.return_value = '[]'
    res = check_drivers()
    assert res["status"] == "healthy"
