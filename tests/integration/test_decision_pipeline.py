import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_high_value_unverified_abstain(client: AsyncClient):
    """
    Test that a high-value transaction from an unverified user 
    is caught by the Hard Constraints layer and results in ABSTAIN.
    """
    payload = {
        "context": {
            "user_id": "user_trial_1",
            "is_verified": False,
            "region": "US"
        },
        "signals": {
            "action_type": "fund_transfer",
            "amount": 15000
        },
        "policy_id": "default"
    }
    
    response = await client.post("/api/v1/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["decision"] == "ABSTAIN"
    assert "Hard Constraint" in data["rationale"]
    assert "hard_constraint_violation" in data["risk_factors"]
    assert data["trace_id"] is not None

@pytest.mark.asyncio
async def test_restricted_region_abstain(client: AsyncClient):
    """
    Test that a restricted region is caught by Hard Constraints.
    """
    payload = {
        "context": {
            "user_id": "user_123",
            "is_verified": True,
            "region": "COUNTRY_X"
        },
        "signals": {
            "action_type": "fund_transfer",
            "amount": 100
        },
        "policy_id": "default"
    }
    
    response = await client.post("/api/v1/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["decision"] == "ABSTAIN"
    assert "restricted region" in data["rationale"].lower()

@pytest.mark.asyncio
async def test_malformed_policy_returns_404(client: AsyncClient):
    """
    Test that requesting a non-existent policy returns a 404.
    """
    payload = {
        "context": {"user_id": "test"},
        "signals": {"action": "test"},
        "policy_id": "non_existent_policy_999"
    }
    
    response = await client.post("/api/v1/decide", json=payload)
    assert response.status_code == 404
