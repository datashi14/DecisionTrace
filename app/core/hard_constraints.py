from typing import Dict, Any, Optional, Tuple
import structlog

logger = structlog.get_logger()

class HardConstraints:
    """
    Enforces deterministic, code-based safety rules that bypass the LLM.
    Guarantees safety for known high-risk invariants.
    """
    
    @staticmethod
    def check(context: Dict[str, Any], signals: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_safe, failure_rationale)
        """
        # Rule 1: High-value unverified transactions
        amount = signals.get("amount", 0)
        is_verified = context.get("is_verified", False)
        
        if amount > 10000 and not is_verified:
            return False, "Hard Constraint: High-value transaction (>10k) rejected for unverified user."
            
        # Rule 2: Restricted Jurisdictions
        restricted_regions = ["COUNTRY_X", "COUNTRY_Y"]
        region = context.get("region")
        if region in restricted_regions:
            return False, f"Hard Constraint: Operation blocked for restricted region: {region}"

        # Rule 3: Missing Critical Identity
        if not context.get("user_id"):
            return False, "Hard Constraint: Missing mandatory user_id."

        return True, None

hard_constraints = HardConstraints()
