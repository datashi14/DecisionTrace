import random
from locust import HttpUser, task, between

class DecisionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def make_decision(self):
        # We simulate a mix of safe and risky transactions to exercise all paths
        is_risky = random.random() < 0.2
        amount = random.randint(100, 50000) if is_risky else random.randint(10, 5000)
        is_verified = random.random() > 0.1
        
        payload = {
            "context": {
                "user_id": f"user_{random.randint(1, 10000)}",
                "is_verified": is_verified,
                "region": random.choice(["US", "UK", "COUNTRY_X", "EU"])
            },
            "signals": {
                "action_type": "fund_transfer",
                "amount": amount
            },
            "policy_id": "default"
        }
        
        with self.client.post("/api/v1/decide", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def health_check(self):
        self.client.get("/health")
