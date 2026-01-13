import requests
import json

def test_decision_flow():
    url = "http://127.0.0.1:8000/api/v1/decide"
    payload = {
        "context": {
            "request_type": "high_risk_operation",
            "user_id": "user_123",
            "operation": "fund_transfer"
        },
        "signals": {
            "amount": 5000,
            "currency": "USD",
            "risk_flags": ["incomplete_data"]
        },
        "policy_id": "default"
    }
    
    print("Testing DecisionTrace Pipeline...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            decision = response.json().get("decision")
            print(f"Outcome: {decision}")
            print(f"Trace ID: {response.json().get('trace_id')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_decision_flow()
