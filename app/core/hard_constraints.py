from typing import Dict, Any, Optional, Tuple
import structlog

logger = structlog.get_logger()

class HardConstraints:
    """
    Enforces deterministic, code-based safety rules that bypass the LLM.
    Guarantees safety for known high-risk invariants.
    """
    
    @staticmethod
    def check(context: Dict[str, Any], signals: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_safe, failure_rationale)
        """
        config = (policy or {}).get("hard_constraints", {})
        
        # Rule 1: High-value transactions
        amount = signals.get("amount", 0)
        is_verified = context.get("is_verified", False)
        
        max_unverified = config.get("max_transaction_unverified", 10000)
        max_verified = config.get("max_transaction_verified", 100000)
        
        if not is_verified and amount > max_unverified:
            return False, f"Hard Constraint: Transaction amount ${amount} exceeds max for unverified user (${max_unverified})."
            
        if is_verified and amount > max_verified:
            return False, f"Hard Constraint: Transaction amount ${amount} exceeds absolute max allowed (${max_verified})."
            
        # Rule 2: Restricted Jurisdictions
        restricted_regions = config.get("restricted_regions", ["COUNTRY_X", "COUNTRY_Y"])
        region = context.get("region")
        if region in restricted_regions:
            return False, f"Hard Constraint: Operation blocked for restricted region: {region}"

        # Rule 3: Missing Critical Identity
        if not context.get("user_id"):
            return False, "Hard Constraint: Missing mandatory user_id."

        return True, None

hard_constraints = HardConstraints()
