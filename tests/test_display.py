import pytest
from unittest.mock import patch
from diagnostics.display import check_display

@patch('diagnostics.display.run_ps')
def test_display_healthy(mock_run_ps):
    mock_run_ps.side_effect = ['[{"Name":"GPU","Status":"OK"}]', '[{"Name":"Monitor","Status":"OK"}]']
    res = check_display()
    assert res["status"] == "healthy"
