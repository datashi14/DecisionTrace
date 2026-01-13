import yaml
import os
import structlog
from typing import Any, Dict, Optional

logger = structlog.get_logger()

class PolicyManager:
    def __init__(self, policies_dir: str = "policies"):
        self.policies_dir = policies_dir
        self.policies: Dict[str, Any] = {}
        self.load_policies()

    def load_policies(self):
        if not os.path.exists(self.policies_dir):
            os.makedirs(self.policies_dir)
            return

        for filename in os.listdir(self.policies_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                policy_id = os.path.splitext(filename)[0]
                with open(os.path.join(self.policies_dir, filename), "r") as f:
                    try:
                        self.policies[policy_id] = yaml.safe_load(f)
                    except Exception as e:
                        logger.error("policy_load_failed", file=filename, error=str(e))
        
        logger.info("policies_loaded", count=len(self.policies))

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        return self.policies.get(policy_id)

policy_manager = PolicyManager()
