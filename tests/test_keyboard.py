import pytest
from unittest.mock import patch
from diagnostics.keyboard import check_keyboard

@patch('diagnostics.keyboard.run_ps')
def test_keyboard_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"KB","Status":"OK"}]'
    res = check_keyboard()
    assert res["status"] == "healthy"
