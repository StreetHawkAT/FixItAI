import pytest
from diagnostics.network import check_network

def test_network_diagnostic_has_status():
    result = check_network()
    
    assert "status" in result, "Network diagnostic must return a 'status' field."
    assert result["status"] in ["healthy", "problem"], "Status must be either 'healthy' or 'problem'."
    assert "category" in result
    assert result["category"] == "network"
    
