import structlog
from typing import Dict, Any
from jinja2 import Template
from app.llm_gateway.client import llm_gateway
from app.core.utils import extract_json

logger = structlog.get_logger()

class EvidencePlanner:
    def __init__(self):
        with open("prompts/evidence_planner.jinja", "r") as f:
            self.template = Template(f.read())

    async def plan(self, input_data: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.template.render(
            input_data=input_data,
            constraints=constraints
        )
        
        # 0. Initial Cost Estimate (Threshold Check)
        # Assuming $0.00001 per token as a rough average for Sonnet
        estimated_input_tokens = len(prompt) // 4
        estimated_cost_usd = (estimated_input_tokens + 1000) * 0.00001 
        
        signals = input_data.get("signals", {})
        transaction_value = signals.get("amount", 0)
        
        # Cost-Aware Risk Gate
        # If the decision cost is more than 0.1% of transaction value or exceeds $5, flag it.
        if estimated_cost_usd > 5.0 or (transaction_value > 0 and estimated_cost_usd > transaction_value * 0.001):
             logger.warning("cost_gate_triggered", estimated_cost=estimated_cost_usd, value=transaction_value)
             # We return a pre-emptive assessment
             return {
                 "recommended_path": "ABSTAIN",
                 "risk_assessment": f"Value of Information (VoI) too low. Cost ${estimated_cost_usd:.2f} relative to value ${transaction_value:.2f}.",
                 "missing_evidence": []
             }

        logger.info("evidence_planning_start")
        result = await llm_gateway.get_structured_decision(
            prompt=prompt,
            system_prompt="You are a safety-first evidence planner."
        )
        
        planned_data = extract_json(result.get("raw_response", "")) or {}
        planned_data["vo_info_assessment"] = {"estimated_cost": estimated_cost_usd}
        
        return planned_data

evidence_planner = EvidencePlanner()
