import pytest
from unittest.mock import patch
from diagnostics.storage import check_storage

@patch('diagnostics.storage.run_ps')
def test_storage_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"DriveLetter":"C","SizeRemaining":50000000000,"Size":100000000000}]'
    res = check_storage()
    assert res["status"] == "healthy"
