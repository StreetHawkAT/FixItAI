import pytest
from unittest.mock import patch
from diagnostics.windows import check_windows

@patch('diagnostics.windows.run_ps')
def test_windows_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[]']
    res = check_windows()
    assert res["status"] == "healthy"
