import pytest
from unittest.mock import patch
from diagnostics.microphone import check_microphone

@patch('diagnostics.microphone.run_ps')
def test_microphone_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[{"Name":"Mic","Status":"OK"}]']
    res = check_microphone()
    assert res["status"] == "healthy"
