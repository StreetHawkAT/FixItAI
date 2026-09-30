import pytest
from unittest.mock import patch
from diagnostics.printer import check_printer

@patch('diagnostics.printer.run_ps')
def test_printer_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[{"Name":"Print","PrinterStatus":3}]']
    res = check_printer()
    assert res["status"] == "healthy"
