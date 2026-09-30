import pytest
from unittest.mock import patch
from diagnostics.performance import check_performance

@patch('diagnostics.performance.run_ps')
def test_performance_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["10", '[{"FreePhysicalMemory":8000000,"TotalVisibleMemorySize":16000000}]']
    res = check_performance()
    assert res["status"] == "healthy"
