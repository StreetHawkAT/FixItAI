import pytest
from unittest.mock import patch
from diagnostics.audio import check_audio

@patch('diagnostics.audio.run_ps')
def test_audio_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", "Running", '[{"Name":"Audio","Status":"OK"}]']
    res = check_audio()
    assert res["status"] == "healthy"
